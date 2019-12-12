# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
from concurrent.futures import ThreadPoolExecutor

import scrapy
from scrapy.pipelines.files import FilesPipeline

from pornhub.items import PornhubItem
from pornhub.lib.DownloadService import DownService
from pornhub.lib.DownloadService import sql_callback
from pornhub.lib.database import DataBase
from pornhub.spiders.all_channel import AllChannel


class PornhubPipeline(object):

    def __init__(self):
        self.t = None

    def open_spider(self, spider: AllChannel):
        self.t = ThreadPoolExecutor(spider.settings.get('DOWN_THREAD'))

    def process_item(self, item, spider: AllChannel):
        if isinstance(item, PornhubItem):
            spider.logger.warning('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            if spider.settings.get('ENABLE_SQL'):
                data_base = DataBase()
                data_base.update_start_down_timestamp_by_title(item.get('file_name'))
                data_base.close()
            # mkdir folder
            file_path = spider.settings.get('FILES_STORE') + os.sep + item.get('file_channel')
            if not os.path.exists(file_path):
                os.makedirs(file_path)

            file_name = item.get('file_name') + '.mp4'
            setting_headers = spider.settings.get('DEFAULT_REQUEST_HEADERS').copy_to_dict()
            setting_headers.pop('Cookie')
            headers = {
                'User-Agent': spider.settings.get('USER_AGENT')
            }
            headers.update(setting_headers)
            f = self.t.submit(
                DownService(spider, headers, item, item.get('file_urls'), file_path + os.sep + file_name).run)
            if spider.settings.get('ENABLE_SQL'):
                f.add_done_callback(sql_callback)


class DownloadVideoPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        if isinstance(item, PornhubItem):
            info.spider.logger.warning('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            if info.spider.settings.get('ENABLE_SQL'):
                data_base = DataBase()
                data_base.update_start_down_timestamp_by_title(item.get('file_name'))
                data_base.close()
            return scrapy.Request(url=item['file_urls'], meta=item)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_channel'] + '/' + request.meta['file_name'] + '.mp4'
        return down_name

    def item_completed(self, results, item, info):
        super(DownloadVideoPipeline, self).item_completed(results, item, info)
        if info.spider.settings.get('ENABLE_SQL'):
            data_base = DataBase()
            data_base.update_end_down_timestamp_by_title(item.get('file_name'))
            data_base.close()
