# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os

import requests

from pornhub.items import PornhubItem
from pornhub.lib.database import DataBase
from pornhub.lib.download_header import random_other_headers
from pornhub.spiders.all_channel import AllChannel

request_log = logging.getLogger('requests')
request_log.setLevel(logging.ERROR)


class PornhubPipeline(object):
    base_url = 'http://127.0.0.1:8800/jsonrpc'

    def process_item(self, item, spider: AllChannel):
        if isinstance(item, PornhubItem):
            file_path = spider.settings.get('ARIA_PATH_PREFIX') + '/' + spider.settings.get(
                'FILES_STORE') + '/' + item.get('file_channel')
            token = 'token:' + spider.settings.get('ARIA_TOKEN')

            view_key = item.get('parent_url').split('viewkey=')[1]
            file_name = '{0}-{1}.mp4'.format(item.get('file_name'), view_key)
            # check file name contains file separator like \ or /
            if os.sep in file_name:
                file_name = file_name.replace(os.sep, '|')

            download_data = {
                'jsonrpc': '2.0',
                'method': 'aria2.addUri',
                'id': '0',
                'params': [token, [item['file_urls']],
                           {'out': file_name, 'dir': file_path, "header": random_other_headers()}]
            }

            spider.logger.info('send to aria2 rpc, item is: %s', item)
            status_code = 300
            while status_code != 200:
                status_code = requests.post(url=self.base_url, json=download_data).status_code
        return item


class SaveDBPipeline(object):

    def __init__(self, is_enable, host, port, user, password):
        self.is_enable = is_enable
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.client = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            is_enable=crawler.settings.get('ENABLE_SQL'),
            host=crawler.settings.get('HOST'),
            port=crawler.settings.get('PORT'),
            user=crawler.settings.get('USER'),
            password=crawler.settings.get('PASSWORD')
        )

    def open_spider(self, spider):
        if self.is_enable:
            self.client = DataBase(self.host, self.port, self.user, self.password)

    def close_spider(self, spider):
        if self.is_enable:
            self.client.close()

    def process_item(self, item, spider):
        if self.is_enable and isinstance(item, PornhubItem):
            self.client.save_my_follow(item.get('file_name'), item.get('file_channel'), item.get('file_urls'),
                                       item.get('parent_url'))
        return item
