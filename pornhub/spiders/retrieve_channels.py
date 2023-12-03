import os

import scrapy
from scrapy.http.response.html import HtmlResponse


class Channel(scrapy.Spider):
    name = 'get'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if os.path.exists('channel.txt'):
            os.remove('channel.txt')

    def start_requests(self):
        yield scrapy.Request('https://www.pornhubpremium.com/channels?o=rk')

    def parse(self, response: HtmlResponse):
        channel_list = []
        description_list = response.css('div.descriptionContainer')
        for item in description_list:
            title = item.css('a::text').get()
            sub_link = item.css('a::attr(href)').get()
            self.logger.info('get channel:{0} ,link is:{1}'.format(title, sub_link))
            save_name = sub_link.split('/')[2]
            channel_list.append(save_name + '\n')

        # determine has next page
        next_page_li = response.css('li.page_next')
        if next_page_li:
            next_page_sub_link = next_page_li.css('a::attr(href)').get()
            next_page_url = response.urljoin(next_page_sub_link)
            self.logger.info('has next page, url is:{0}'.format(next_page_url))
            yield scrapy.Request(next_page_url)

        with open('channel.txt', 'a+') as f:
            f.writelines(channel_list)
