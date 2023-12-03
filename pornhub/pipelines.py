# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import base64
import os
import shlex
import shutil
import subprocess

import m3u8

from pornhub.items import PornhubItem
from pornhub.lib.database import DataBase
from pornhub.spiders.all_channel import AllChannel


class PornhubPipeline(object):
    def prepare_folder(self, item: PornhubItem, spider: AllChannel) -> dict:
        # temp path to store m3u8 downloaded ts files
        temp_store_path = base64.urlsafe_b64encode(item.get('file_name').encode()).decode()
        view_key = item.get('parent_url').split('viewkey=')[1]
        file_name = f'{item.get("file_name")}-{view_key}.mp4'
        # check file name contains file separator like \ or /
        if os.sep in file_name:
            file_name = file_name.replace(os.sep, '|')
        # final path to store combined mp4 files
        final_store_path = os.path.join(
            spider.settings.get('PATH_PREFIX'), spider.settings.get('FILES_STORE'), item.get('file_channel')
        )
        if not os.path.exists(final_store_path):
            spider.logger.info('create folder %s', final_store_path)
            os.makedirs(final_store_path)
        return {'temp_store_path': temp_store_path, 'file_name': file_name, 'final_store_path': final_store_path}

    def process_item(self, item: PornhubItem, spider: AllChannel):
        if not isinstance(item, PornhubItem):
            return item
        prepared_info = self.prepare_folder(item, spider)
        spider.logger.info('start to download, item is: %s', item)
        m3u8_list_file_name = f'{item.get("file_name")}.txt'
        with open(m3u8_list_file_name, 'w') as down_txt:
            for segment_info in m3u8.load(
                m3u8.load(item.get("file_urls")).playlists[0].absolute_uri
            ).segments:  # type:m3u8.Segment
                down_txt.write(f'{segment_info.absolute_uri}\n')
        subprocess.run(
            shlex.split(f'aria2c -i "{m3u8_list_file_name}" -j 10 -d {prepared_info.get("temp_store_path")}'),
            check=True,
            capture_output=True,
        )

        final_mp4_full_path = os.path.join(prepared_info.get('final_store_path'), prepared_info.get('file_name'))
        # TODO;check md5, decide copy or ignore,avoid repeat merge
        if os.path.exists(final_mp4_full_path):
            spider.logger.error('file exists, item: %s', item)
            return item
        with open(final_mp4_full_path, 'ab') as final_video:
            for combine_file_name in sorted(
                os.listdir(prepared_info.get("temp_store_path")),
                key=lambda x: int(x.split('-')[1]),
            ):
                with open(
                    os.path.join(prepared_info.get("temp_store_path"), combine_file_name),
                    'rb',
                ) as video_file:
                    final_video.write(video_file.read())
        # clean folder
        shutil.rmtree(prepared_info.get("temp_store_path"))


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
            password=crawler.settings.get('PASSWORD'),
        )

    def open_spider(self, spider):
        if self.is_enable:
            self.client = DataBase(self.host, self.port, self.user, self.password)

    def close_spider(self, spider):
        if self.is_enable:
            self.client.close()

    def process_item(self, item, spider):
        if self.is_enable and isinstance(item, PornhubItem):
            self.client.save_my_follow(
                item.get('file_name'), item.get('file_channel'), item.get('file_urls'), item.get('parent_url')
            )
        return item
