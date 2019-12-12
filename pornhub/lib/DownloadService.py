from concurrent.futures import Future

import requests

from pornhub.items import PornhubItem
from pornhub.lib.database import DataBase
from pornhub.spiders.all_channel import AllChannel


class DownService:

    def __init__(self, spider: AllChannel, headers: dict, item: PornhubItem, url: str, file_name: str):
        super().__init__()
        self.url = url
        self.file_name = file_name
        self.item = item
        self.headers = headers
        self.spider = spider

    def run(self) -> str:
        response = requests.get(url=self.url, headers=self.headers, stream=True)
        with open(self.file_name, 'wb') as f:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
        return self.item.get('file_name')


def sql_callback(obj: Future):
    data_base = DataBase()
    data_base.update_end_down_timestamp_by_title(obj.result())
    data_base.close()
