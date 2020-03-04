# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os
import time

import requests

from pornhub.items import PornhubItem
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
            concurrent_download = spider.settings.get('CONCURRENT_DOWNLOAD')

            view_key = item.get('parent_url').split('viewkey=')[1]
            file_name = '{0}-{1}.mp4'.format(item.get('file_name'), view_key)
            # check file name contains file separator like \ or /
            if os.sep in file_name:
                file_name = file_name.replace(os.sep, '|')

            download_data = {
                'jsonrpc': '2.0',
                'method': 'aria2.addUri',
                'id': '0',
                'params': [token, [item['file_urls']], {'out': file_name, 'dir': file_path}]
            }
            status_data = {
                'jsonrpc': '2.0',
                'method': 'aria2.getGlobalStat',
                'id': '0',
                'params': [token]
            }

            while True:
                response = requests.post(url=self.base_url, json=status_data)
                active = response.json().get('result').get('numActive')
                if int(active) < concurrent_download:
                    break
                spider.logger.debug('aria2 has downloading, sleep')
                time.sleep(30)

            spider.logger.info('send to aria2 rpc, item is: %s', item)
            status_code = requests.post(url=self.base_url, json=download_data).status_code
            if status_code != 200:
                spider.logger.error('send to aria2 download failed, item is: %s', item)
