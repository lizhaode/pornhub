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
            sub_link = item.css('a.usernameLink').css('a::attr(href)').extract_first() + '/videos/upload'
            yield scrapy.Request('https://www.pornhubpremium.com' + sub_link, callback=self.model_page, priority=10)

    def model_page(self, response: HtmlResponse):
        video_sum_element = response.css('div.showingInfo').css('span.totalSpan')
        # some porn star hasn't show video number
        page_number = 1
        if video_sum_element:
            video_sum = video_sum_element.css('::text').extract_first()
            sum_number = int(video_sum)
            page_number = math.ceil(sum_number / 40)
        # url contains page means load all videos || num == 1, start parse
        if 'page' in response.url or page_number == 1:
            li_list = response.css('div.videoUList').css('ul').css('li')
            for li_tag in li_list:  # type: SelectorList
                a_tag = li_tag.css('span.title').css('a')
                video_title = a_tag.css('::text').extract_first()
                video_url = a_tag.css('::attr(href)').extract_first()
                real_url = 'https://www.pornhubpremium.com' + video_url
                self.logger.info('send [%s] ,url: %s', video_title, video_url)
                yield scrapy.Request(real_url, callback=self.video_page, priority=100)
        else:
            # url not contains page and num > 1 means need load all videos
            new_link = '{0}?page={1}'.format(response.url, page_number)
            yield scrapy.Request(new_link, callback=self.model_page, priority=10)

    def video_page(self, response: HtmlResponse):
        video_title = response.css('h1.title').css('span::text').extract_first()
        video_channel = response.css('div.video-actions-container').css('div.usernameWrap.clearfix').css(
            'a::text').extract_first()
        js = response.css('div.video-wrapper').css('#player').css('script').extract_first()
        prepare_js = js.split('<script type="text/javascript">')[1].split('loadScriptUniqueId')[0]
        exec_js = 'function f(){' + prepare_js + 'if (typeof (quality_2160p) != "undefined") { return quality_2160p; ' \
                                                 '} else if (typeof (quality_1440p) != "undefined") { return ' \
                                                 'quality_1440p;} else if (typeof (quality_1080p) != "undefined") {' \
                                                 'return quality_1080p;} else if (typeof (quality_720p) != ' \
                                                 '"undefined") { return quality_720p; } else { return ''; }} '
        f = js2py.eval_js(exec_js)
        video_url = f()
        if video_url is not None:
            self.logger.info('parse [%s] success, url: %s', video_title, video_url)
            if self.settings.get('ENABLE_SQL'):
                result = self.data_base.select_all_by_title_my_follow(video_title)
                if len(result) != 0:
                    for line in result:
                        self.logger.error('has duplicate record: %s', line)
                else:
                    self.data_base.save_my_follow(video_title, video_channel, video_url, response.url)
            yield PornhubItem(file_urls=video_url, file_name=video_title, file_channel=video_channel)
