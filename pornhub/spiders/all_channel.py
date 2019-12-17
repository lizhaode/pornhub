import js2py
import scrapy
from scrapy.exceptions import NotSupported
from scrapy.http.response.html import HtmlResponse

from pornhub.items import PornhubItem
from pornhub.lib.database import DataBase


class AllChannel(scrapy.Spider):
    name = 'all'

    def start_requests(self):
        channel_number = self.settings.get('CHANNEL_NUMBER')
        channel_list = []
        base_url = 'https://www.pornhubpremium.com/channels/{0}/videos?o=ra'
        with open('channel.txt') as f:
            for channel in f:
                channel = channel.strip()
                if channel != '':
                    channel_list.append(channel)
        # check CHANNEL_NUMBER is smaller than list length
        if isinstance(channel_number, int) and len(channel_list) < channel_number:
            raise NotSupported('CHANNEL_NUMBER config is bigger than website channel list')

        if channel_number == 'ALL':
            for i in channel_list:
                yield scrapy.Request(base_url.format(i))
        else:
            for i in range(channel_number):
                yield scrapy.Request(base_url.format(channel_list[i]))

    def parse(self, response: HtmlResponse):
        videos_list = response.css('ul.videos.row-5-thumbs.videosGridWrapper')
        video_css = videos_list.css('span.title')
        for item in video_css:
            video_sub_link = item.css('a::attr(href)').extract_first()
            video_url = response.urljoin(video_sub_link)
            self.logger.warning('send to parse real video, url is:{0}'.format(video_url))
            yield scrapy.Request(video_url, callback=self.video_page)

        # determine has next page
        next_page_li = response.css('li.page_next')
        if next_page_li:
            next_page_sub_link = next_page_li.css('a::attr(href)').extract_first()
            next_page_url = response.urljoin(next_page_sub_link)
            yield scrapy.Request(next_page_url)

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
            self.logger.warning('parse {0} video url:{1}'.format(video_title, video_url))
            if self.settings.get('ENABLE_SQL'):
                data_base = DataBase()
                result = data_base.select_all_by_title(video_title)
                if len(result) != 0:
                    for line in result:
                        self.logger.error('has duplicate record: %s', line)
                else:
                    data_base.save(video_title, video_channel, video_url, response.url)
                    data_base.close()
            yield PornhubItem(file_urls=video_url, file_name=video_title, file_channel=video_channel)
