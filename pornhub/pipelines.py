# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import shlex
import subprocess

from pornhub.items import PornhubItem
from pornhub.spiders.all_channel import AllChannel


class PornhubPipeline(object):
    def process_item(self, item: PornhubItem, spider: AllChannel):
        if not isinstance(item, PornhubItem):
            return item

        # prepare
        view_key = item.get('parent_url').split('viewkey=')[1]
        file_name = f'{item.get("file_name")}-{view_key}.mp4'
        # check file name contains file separator like \ or /
        if os.sep in file_name:
            file_name = file_name.replace(os.sep, '|')
        # final path to store combined mp4 files
        final_store_path = os.path.join(
            spider.settings.get('PATH_PREFIX'), spider.settings.get('FILES_STORE'), item.get('file_channel')
        )

        spider.logger.info('start to download, item is: %s', item)
        subprocess.run(
            shlex.split(f'aria2c "{item.get("file_urls")}" -x 3 -d {final_store_path} -o "{file_name}"'),
            check=True,
            capture_output=True,
        )
