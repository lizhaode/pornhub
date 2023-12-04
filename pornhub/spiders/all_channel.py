import js2py
import scrapy
from scrapy.exceptions import NotSupported
from scrapy.http.response.html import HtmlResponse
from scrapy.selector import SelectorList

from pornhub.items import PornhubItem


class AllChannel(scrapy.Spider):
    name = 'all'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

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
        for item in video_css:  # type: SelectorList
            video_sub_link = item.css('a::attr(href)').get()
            video_url = response.urljoin(video_sub_link)
            title = item.css('a::text').get()
            self.logger.info('send [%s] to parse real video', title)
            yield scrapy.Request(video_url, callback=self.video_page, priority=100)

        # determine has next page
        next_page_li = response.css('li.page_next')
        if next_page_li:
            next_page_sub_link = next_page_li.css('a::attr(href)').get()
            next_page_url = response.urljoin(next_page_sub_link)
            yield scrapy.Request(next_page_url)

    def video_page(self, response: HtmlResponse):
        video_title = response.css('h1.title').css('span::text').get()
        video_channel = (
            response.css('div.video-actions-container').css('div.usernameWrap.clearfix').css('a::text').get()
        )
        js = response.css('div.video-wrapper').css('#player').css('script').get()
        data_video_id = response.css('div.video-wrapper').css('#player::attr(data-video-id)').get()
        prepare_js = js.split('<script type="text/javascript">')[1].split('loadScriptUniqueId')[0]
        exec_js = '{0}\nqualityItems_{1};'.format(prepare_js, data_video_id)
        js_result = js2py.eval_js(exec_js)  # type: js2py.base.JsObjectWrapper
        quality_items = js_result.to_list()  # type: list
        quality = quality_items[-1]['text'].split('p')[0]
        if int(quality) >= 720:
            video_url = quality_items[-1]['url']
            self.logger.info('parse [%s] success, url: %s', video_title, video_url)
            if self.settings.get('ENABLE_SQL'):
                result = self.data_base.select_all_by_title_my_follow(video_title)
                if len(result) != 0:
                    for line in result:
                        self.logger.error('has duplicate record: %s', line)
                else:
                    self.data_base.save_my_follow(video_title, video_channel, video_url, response.url)
            yield PornhubItem(file_urls=video_url, file_name=video_title, file_channel=video_channel)
