import js2py
import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList

from pornhub.items import PornhubItem


class MyFollow(scrapy.Spider):
    name = 'myfollow'

    def start_requests(self):
        yield scrapy.Request('https://www.pornhubpremium.com/users/daiqiangbudainiu/subscriptions')

    def parse(self, response: HtmlResponse):
        model_filter_list = self.settings.getlist('MODEL_FILTER_LIST')
        li_tag_list = response.css('div.sectionWrapper').css('ul#moreData').css('li')
        for item in li_tag_list:  # type: SelectorList
            sub_link = item.css('a.usernameLink').css('a::attr(href)').get()
            model_name = sub_link.split('/')[-1]
            if model_name in model_filter_list or len(model_filter_list) == 0:
                # filter user, model, pornStar
                if '/model/' in sub_link:
                    yield scrapy.Request(response.urljoin(sub_link + '/videos/upload'), callback=self.model_page,
                                         priority=10)
                    yield scrapy.Request(response.urljoin(sub_link + '/videos/premium'), callback=self.model_page,
                                         priority=10)

                elif '/pornstar/' in sub_link:
                    yield scrapy.Request(response.urljoin(sub_link + '/videos/upload'), callback=self.porn_star_page,
                                         priority=10)
                    yield scrapy.Request(response.urljoin(sub_link + '/videos/premium'), callback=self.porn_star_page,
                                         priority=10)
                else:
                    yield scrapy.Request(response.urljoin(sub_link + '/videos/public'), callback=self.model_page,
                                         priority=10)

    def model_page(self, response: HtmlResponse):
        # parse current page
        video_list = self.check_is_hd_video(response)
        for i in video_list:
            yield scrapy.Request(response.urljoin(i), callback=self.video_page, priority=100)
        # check has "Load More" button
        more_button = response.css('#moreDataBtnStream')
        if more_button:
            max_page = more_button.css('::attr(data-maxpage)').get()
            load_more_ori_str = more_button.css('::attr(onclick)').get()
            ajax_url = load_more_ori_str.split("'")[1]
            for i in range(2, int(max_page) + 1):
                new_link = '{0}&page={1}'.format(response.urljoin(ajax_url), i)
                yield scrapy.Request(new_link, callback=self.ajax_model_page, priority=10)

    def porn_star_page(self, response: HtmlResponse):
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

    def ajax_model_page(self, response: HtmlResponse):
        model_info_list = response.css('li.pcVideoListItem')
        for item in model_info_list:  # type: SelectorList
            hd_span = item.css('div.phimage').css('span.hd-thumbnail')
            if hd_span:
                video_url = item.css('span.title').css('a::attr(href)').get()
                yield scrapy.Request(response.urljoin(video_url), callback=self.video_page, priority=100)

    def video_page(self, response: HtmlResponse):
        # some video has "Watch Full Video" button
        full_video_button = response.css("#trailerFullLengthDownload")
        video_title = response.css('h1.title').css('span::text').get()
        video_channel = response.css('div.video-actions-container').css('div.usernameWrap.clearfix').css(
            'a::text').get()
        if full_video_button:
            button_title = full_video_button.css('::attr(data-title)').get()
            if button_title == 'Watch Full Video':
                full_url = full_video_button.css('::attr(href)').get()
                self.logger.info('%s detected full video, original name: %s', video_channel, video_title)
                yield scrapy.Request(full_url, callback=self.video_page, priority=100)
                return
        self.logger.debug('get model: %s, title: %s', video_channel, video_title)
        player_id_element = response.css('#player')
        js = player_id_element.css('script').get()
        data_video_id = player_id_element.css('::attr(data-video-id)').get()
        prepare_js = js.split('<script type="text/javascript">')[1].split('playerObjList')[0]
        exec_js = '{0}\nqualityItems_{1};'.format(prepare_js, data_video_id)
        js_result = js2py.eval_js(exec_js)  # type: js2py.base.JsObjectWrapper
        quality_items = js_result.to_list()  # type: list
        video_url = quality_items[-1]['url']
        yield PornhubItem(file_urls=video_url, file_name=video_title, file_channel=video_channel,
                          parent_url=response.url)

    def check_is_hd_video(self, response: HtmlResponse) -> list:
        hd_video_list = []
        li_list = response.css('div.videoUList').css('ul').css('li')
        for li_tag in li_list:  # type: SelectorList
            hd_span = li_tag.css('div.phimage').css('span.hd-thumbnail')
            if hd_span:
                video_url = li_tag.css('span.title').css('a::attr(href)').get()
                hd_video_list.append(video_url)
        return hd_video_list
