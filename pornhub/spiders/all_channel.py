import json
from typing import Any

import scrapy
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList
from zhconv import convert

from pornhub.items import PornhubItem


class AllChannel(scrapy.Spider):
    name = 'channel'

    def start_requests(self):
        for channel in self.settings.get('CHANNEL_LIST'):
            yield scrapy.Request(f'https://www.pornhub.com/channels/{channel}')

    def parse(self, response: HtmlResponse, **kwargs: Any):
        videos_list = response.css('ul.videos.row-5-thumbs.videosGridWrapper').css('span.title')
        for item in videos_list:  # type: SelectorList
            video_sub_link = item.css('a::attr(href)').get()
            video_url = response.urljoin(video_sub_link)
            title = item.css('a::text').get().strip()
            self.logger.info('send [%s] to parse real video', title)
            yield scrapy.Request(video_url, callback=self.video_page, priority=100)

        # determine has next page
        next_page = response.css('li.page_next')
        if next_page:
            next_page_sub_link = next_page.css('a::attr(href)').get()
            yield scrapy.Request(response.urljoin(next_page_sub_link))

    def video_page(self, response: HtmlResponse, **kwargs: Any):
        # some video has "Watch Full Video" button, ignore now
        video_title = convert(response.css('span.inlineFree::text').get(), 'zh-cn')
        print(video_title)
        video_channel = response.css('div.userInfo').css('a::text').get()
        self.logger.info('get channel: %s, title: %s', video_channel, video_title)
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
