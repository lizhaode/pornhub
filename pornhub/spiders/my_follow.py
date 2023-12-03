from typing import Any

import js2py
import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList
from zhconv.zhconv import convert

from pornhub.items import PornhubItem


class MyFollow(scrapy.Spider):
    name = 'myfollow'

    def start_requests(self):
        yield scrapy.Request('https://www.pornhub.com/login')

    def parse(self, response: HtmlResponse, **kwargs: Any):
        body = {
            'username': self.settings.get('PORN_USER'),
            'password': self.settings.get('PORN_PWD'),
            'token': response.css('input#token::attr(value)').get(),
            'redirect': response.css('form.js-loginFormModal.js-loginForm').css('input.js-redirect::attr(value)').get(),
            'from': 'pc_login_modal_:index',
            'user_id': '',
            'intended_action': '',
            'taste_profile': '',
        }
        yield scrapy.FormRequest(
            url='https://www.pornhub.com/front/authenticate', formdata=body, callback=self.parse_subscription
        )

    def parse_subscription(self, response: HtmlResponse, **kwargs: Any):
        if response.json().get('success') == '1':
            yield scrapy.Request(
                'https://www.pornhub.com/users/daiqiangbudainiu/subscriptions', callback=self.start_parse
            )

    def start_parse(self, response: HtmlResponse, **kwargs: Any):
        model_filter_list = self.settings.getlist('MODEL_FILTER_LIST')
        li_tag_list = response.css('div.sectionWrapper').css('ul#moreData').css('li')
        for item in li_tag_list:  # type: SelectorList
            sub_link = item.css('a.usernameLink').css('a::attr(href)').get()
            model_name = sub_link.split('/')[-1]
            if model_name in model_filter_list or len(model_filter_list) == 0:
                # filter user, model, pornStar
                if '/model/' in sub_link:
                    yield scrapy.Request(response.urljoin(sub_link + '/videos'), callback=self.model_page, priority=10)
                elif '/pornstar/' in sub_link:
                    yield scrapy.Request(
                        response.urljoin(sub_link + '/videos/upload'), callback=self.porn_star_page, priority=10
                    )
                    yield scrapy.Request(
                        response.urljoin(sub_link + '/videos/premium'), callback=self.porn_star_page, priority=10
                    )
                else:
                    yield scrapy.Request(
                        response.urljoin(sub_link + '/videos/public'), callback=self.model_page, priority=10
                    )

    def model_page(self, response: HtmlResponse, **kwargs: Any):
        # 1.parse current page
        for video_item in response.css('div.videoUList').css('li.pcVideoListItem'):  # type:SelectorList
            video_url = video_item.css('span.title').css('a::attr(href)').get()
            yield scrapy.Request(response.urljoin(video_url), callback=self.video_page, priority=100)

        # 2.check next page
        next_url = response.css('li.page_next').css('a::attr(href)').get()
        if next_url:
            yield scrapy.Request(response.urljoin(next_url), callback=self.model_page, priority=50)

    def porn_star_page(self, response: HtmlResponse, **kwargs: Any):
        # porn star type no need page number,because next page=2 not show all 2 page videos
        video_list = self.check_is_hd_video(response)
        for i in video_list:
            yield scrapy.Request(response.urljoin(i), callback=self.video_page, priority=100)
        # check has next button
        page_element = response.css('div.pagination3')
        if page_element:
            # if in last page, page_next css not exist
            next_element = page_element.css('li.page_next')
            if next_element:
                next_url = next_element.css('a::attr(href)').get()
                yield scrapy.Request(response.urljoin(next_url), callback=self.porn_star_page, priority=10)

    def video_page(self, response: HtmlResponse, **kwargs: Any):
        # some video has "Watch Full Video" button, ignore now
        video_title = convert(response.css('h1.title').css('span::text').get(), 'zh-cn')
        video_channel = response.css('div.userInfo').css('a::text').get()
        self.logger.info('get model: %s, title: %s', video_channel, video_title)
        player_id_element = response.css('div#player')
        prepare_js = (
            player_id_element.css('script')
            .get()
            .split('<script type="text/javascript">')[1]
            .split('playerObjList')[0]
            .strip()
        )
        exec_js = '{0}\nflashvars_{1};'.format(prepare_js, player_id_element.css('::attr(data-video-id)').get())
        video_info_list = js2py.eval_js(exec_js).to_dict().get('mediaDefinitions')
        # make sure dict structure {quality:'1080'}
        highest_quality = sorted(
            video_info_list,
            key=lambda x: int(x.get('quality')) if isinstance(x.get('quality'), str) else 0,
            reverse=True,
        )[0]
        if int(highest_quality.get('quality')) >= 1080:
            yield PornhubItem(
                file_urls=highest_quality.get('videoUrl'),
                file_name=video_title,
                file_channel=video_channel,
                parent_url=response.url,
            )
