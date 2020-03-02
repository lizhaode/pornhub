import math

import js2py
import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList

from pornhub.items import PornhubItem
from pornhub.lib.database import DataBase


class MyFollow(scrapy.Spider):
    name = 'myfollow'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.data_base = None

    def start_requests(self):
        if self.settings.get('ENABLE_SQL'):
            self.data_base = DataBase()
        yield scrapy.Request('https://www.pornhubpremium.com/users/daiqiangbudainiu/subscriptions')

    def parse(self, response: HtmlResponse):
        li_tag_list = response.css('div.sectionWrapper').css('ul#moreData').css('li')
        for item in li_tag_list:  # type: SelectorList
            sub_link = item.css('a.usernameLink').css('a::attr(href)').get()
            # filter user, model, pornStar
            if '/model/' in sub_link or '/pornstar/' in sub_link:
                yield scrapy.Request(response.urljoin(sub_link + '/videos/upload'), callback=self.model_page,
                                     priority=10)
            else:
                yield scrapy.Request(response.urljoin(sub_link + '/videos/public'), callback=self.model_page,
                                     priority=10)

    def model_page(self, response: HtmlResponse):
        if '/model/' in response.url or '/users' in response.url:
            video_sum_element = response.css('div.showingInfo')
            # some porn star hasn't show video number
            page_number = 1
            if video_sum_element:
                video_sum = video_sum_element.css('.totalSpan::text').get()
                sum_number = int(video_sum)
                page_number = math.ceil(sum_number / 40)
            # url contains page means load all videos || num == 1, start parse
            if page_number == 1:
                li_list = response.css('div.videoUList').css('ul').css('li')
                for li_tag in li_list:  # type: SelectorList
                    a_tag = li_tag.css('span.title').css('a')
                    video_url = a_tag.css('::attr(href)').get()
                    real_url = response.urljoin(video_url)
                    yield scrapy.Request(real_url, callback=self.video_page, priority=100)
            else:
                # num > 1 means need load left videos
                for i in range(2, page_number + 1):
                    new_link = '{0}/ajax?o=best&page={1}'.format(response.url, i)
                    yield scrapy.Request(new_link, callback=self.ajax_model_page, priority=10)
        else:
            # porn star type no need page number,because next page=2 not show all 2 page videos
            li_list = response.css('div.videoUList').css('ul').css('li')
            for li_tag in li_list:  # type: SelectorList
                a_tag = li_tag.css('span.title').css('a')
                video_url = a_tag.css('::attr(href)').get()
                real_url = response.urljoin(video_url)
                yield scrapy.Request(real_url, callback=self.video_page, priority=100)
            # check has next button
            page_element = response.css('div.pagination3')
            if page_element:
                # if in last page, page_next css not exist
                next_element = page_element.css('li.page_next')
                if next_element:
                    next_url = next_element.css('a::attr(href)').get()
                    yield scrapy.Request(response.urljoin(next_url), callback=self.model_page, priority=10)

    def ajax_model_page(self, response: HtmlResponse):
        model_info_list = response.css('li.pcVideoListItem')
        for item in model_info_list:  # type: SelectorList
            video_url = item.css('span.title').css('a::attr(href)').get()
            yield scrapy.Request(response.urljoin(video_url), callback=self.video_page, priority=100)

    def video_page(self, response: HtmlResponse):
        video_title = response.css('h1.title').css('span::text').get()
        video_channel = response.css('div.video-actions-container').css('div.usernameWrap.clearfix').css(
            'a::text').get()
        self.logger.info('get model: %s, title: %s', video_channel, video_title)
        js = response.css('div.video-wrapper').css('#player').css('script').get()
        data_video_id = response.css('div.video-wrapper').css('#player::attr(data-video-id)').get()
        prepare_js = js.split('<script type="text/javascript">')[1].split('loadScriptUniqueId')[0]
        exec_js = '{0}\nqualityItems_{1};'.format(prepare_js, data_video_id)
        js_result = js2py.eval_js(exec_js)  # type: js2py.base.JsObjectWrapper
        quality_items = js_result.to_list()  # type: list
        quality = quality_items[-1]['text'].split('p')[0]
        if int(quality) >= 720:
            video_url = quality_items[-1]['url']
            if self.settings.get('ENABLE_SQL'):
                result = self.data_base.select_all_by_title_my_follow(video_title)
                if len(result) != 0:
                    for line in result:
                        self.logger.error('has duplicate record: %s', line)
                else:
                    self.data_base.save_my_follow(video_title, video_channel, video_url, response.url)
            yield PornhubItem(file_urls=video_url, file_name=video_title, file_channel=video_channel,
                              parent_url=response.url)
