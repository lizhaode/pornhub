import json
from typing import Any

import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList
from zhconv.zhconv import convert

from pornhub.items import PornhubItem


class MyFollow(scrapy.Spider):
    name = 'model'

    def start_requests(self):
        for model in self.settings.getlist('MODEL_LIST'):
            yield scrapy.Request(f'https://www.pornhub.com/model/{model}/videos')
        for porn_star in self.settings.getlist('PORN_STAR_LIST'):
            yield scrapy.Request(f'https://cn.pornhub.com/pornstar/{porn_star}/videos/upload')

    def parse(self, response: HtmlResponse, **kwargs: Any):
        # 1.parse current page
        for video_item in response.css('div.videoUList').css('li.pcVideoListItem'):  # type:SelectorList
            video_url = video_item.css('span.title').css('a::attr(href)').get()
            yield scrapy.Request(response.urljoin(video_url), callback=self.video_page, priority=100)

        # 2.check next page
        next_url = response.css('li.page_next').css('a::attr(href)').get()
        if next_url:
            yield scrapy.Request(response.urljoin(next_url), priority=50)

    def video_page(self, response: HtmlResponse, **kwargs: Any):
        # some video has "Watch Full Video" button, ignore now
        video_title = convert(response.css('h1.title').css('span::text').get(), 'zh-cn')
        video_channel = response.css('div.userInfo').css('a::text').get()
        self.logger.info('get model: %s, title: %s', video_channel, video_title)
        media_definitions = json.loads(
            '{' + response.css('div#player').css('script::text').get().strip().splitlines()[0].strip(';').split(' {')[1]
        ).get('mediaDefinitions')

        # extract mp4 format
        yield scrapy.Request(
            [i.get('videoUrl') for i in media_definitions if i.get('format') == 'mp4'][0],
            dont_filter=True,
            cb_kwargs={'file_name': video_title, 'file_channel': video_channel, 'parent_url': response.url},
            callback=self.send_to_pipeline,
        )

    def send_to_pipeline(self, response: HtmlResponse, **kwargs: Any):
        highest_quality = sorted(
            response.json(),
            key=lambda x: int(x.get('quality')),
            reverse=True,
        )[0]
        if int(highest_quality.get('quality')) >= 720:
            yield PornhubItem(
                file_urls=highest_quality.get('videoUrl'),
                file_name=response.cb_kwargs.get('file_name'),
                file_channel=response.cb_kwargs.get('file_channel'),
                parent_url=response.cb_kwargs.get('parent_url'),
            )
        else:
            self.logger.warning('quality low, not download title: %s', response.cb_kwargs.get('file_name'))
