# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os
import time

import requests
import scrapy
from scrapy.pipelines.files import FilesPipeline

from pornhub.items import PornhubItem
from pornhub.spiders.all_channel import AllChannel

log = logging.getLogger(__name__)

request_log = logging.getLogger('requests')
request_log.setLevel(logging.ERROR)


class PornhubPipeline(object):
    base_url = 'http://127.0.0.1:8800/jsonrpc'

    def process_item(self, item, spider: AllChannel):
        if isinstance(item, PornhubItem):
            file_path = spider.settings.get('ARIA_PATH_PREFIX') + '/' + spider.settings.get(
                'FILES_STORE') + '/' + item.get('file_channel')
            view_key = item.get('parent_url').split('viewkey=')[1]
            file_name = '{0}-{1}.mp4'.format(item.get('file_name'), view_key)
            # check file name contains file separator like \ or /
            if os.sep in file_name:
                file_name = file_name.replace(os.sep, '|')

            token = 'token:' + spider.settings.get('ARIA_TOKEN')
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
            # ensure aria2 concurrent download 20 videos
            while True:
                response = requests.post(url=self.base_url, json=status_data)
                active = response.json().get('result').get('numActive')
                if int(active) <= 20:
                    break
                time.sleep(5)

            log.info('send to aria2 rpc, args %s', download_data)
            requests.post(url=self.base_url, json=download_data)

    def check_download_success(self, gid: str, token: str) -> dict:
        result = {
            'status': 'downloading',
            'error_code': '',
            'error_message': ''
        }
        status_data = {
            'jsonrpc': '2.0',
            'method': 'aria2.tellStatus',
            'id': '0',
            'params': [token, gid, ['status', 'errorCode', 'errorMessage']]
        }
        response = requests.post(url=self.base_url, json=status_data)
        aria_dict = response.json().get('result')
        result['status'] = aria_dict.get('status')
        if result['status'] == 'error':
            result['error_code'] = aria_dict.get('errorCode')
            result['error_message'] = aria_dict.get('errorMessage')
            return result
        elif result['status'] == 'complete':
            return result
        else:
            return result

    def remove_download(self, gid: str, token: str) -> None:
        remove_data = {
            'jsonrpc': '2.0',
            'method': 'aria2.removeDownloadResult',
            'id': '0',
            'params': [token, gid]
        }
        response = requests.post(url=self.base_url, json=remove_data)
        if response.status_code != 200 and response.json().get('result') != 'OK':
            raise ValueError('remove download from aria2 fail')


class DownloadVideoPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        if isinstance(item, PornhubItem):
            # check file name contains file separator like \ or /
            if os.sep in item['file_name']:
                item['file_name'] = item['file_name'].replace(os.sep, '|')
            info.spider.logger.info('receive download task, name: {0}'.format(item['file_name']))
            return scrapy.Request(url=item['file_urls'], meta=item, priority=200)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_channel'] + '/' + request.meta['file_name'] + '.mp4'
        return down_name
