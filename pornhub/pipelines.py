# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
from scrapy.pipelines.files import FilesPipeline
from pornhub.items import PornhubItem


class PornhubPipeline(object):
    def process_item(self, item, spider):
        return item


class DownloadVideoPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        if isinstance(item, PornhubItem):
            info.spider.logger.warn('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            return scrapy.Request(url=item['file_urls'], meta=item)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_channel'] + '/' + request.meta['file_name'] + '.mp4'
        return down_name
