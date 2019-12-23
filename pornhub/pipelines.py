# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

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
            file_name = item.get('file_name') + '.mp4'
            # check file name contains file separator like \ or /
            if os.sep in file_name:
                file_name = file_name.replace(os.sep, '|')

            token = 'token:' + spider.settings.get('ARIA_TOKEN')
            aria_data = {
                'jsonrpc': '2.0',
                'method': 'aria2.addUri',
                'id': '0',
                'params': [token, [item['file_urls']], {'out': file_name, 'dir': file_path}]
            }
            log.info('send to aria2 rpc, args %s', aria_data)
            response = requests.post(url=self.base_url, json=aria_data)
            gid = response.json().get('result')

            retry_times = 0
            while True:
                if retry_times > spider.settings.get('RETRY_TIMES'):
                    log.error('over retry times, [%s] download fail', file_name)
                    break
                time.sleep(3)
                result = self.check_download_success(gid, token)
                if result.get('status') == 'complete':
                    log.info('%s download success', item.get('file_name'))
                    break
                elif result.get('status') == 'error':
                    fail_code = result.get('error_code')
                    fail_message = result.get('error_message')
                    self.remove_download(gid, token)
                    log.info('%s download fail, fail code is: %s, message is: %s', item.get('file_name'), fail_code,
                             fail_message)
                    if fail_code == '13':
                        break
                    elif fail_code == '22':
                        break
                    retry_resp = requests.post(url=self.base_url, json=aria_data)
                    gid = retry_resp.json().get('result')
                    retry_times += 1

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
            info.spider.logger.info('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            return scrapy.Request(url=item['file_urls'], meta=item)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_channel'] + '/' + request.meta['file_name'] + '.mp4'
        return down_name
