from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy.orm.session import sessionmaker
from pornhub.lib.entity.channelDO import Channel
from typing import List

HOST = ''
PORT = 3306
USER = 'root'
PASSWORD = ''


class DataBase:

    def __init__(self):
        self.connect_url = 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}' \
            .format(username=USER, password=quote_plus(PASSWORD), host=HOST, port=PORT, database='pornhub')
        self.engine = create_engine(self.connect_url)
        self.session_maker = sessionmaker(self.engine)
        self.session = self.session_maker()

    def select_all_by_title(self, title: Channel.title) -> List[Channel]:
        return self.session.query(Channel).filter_by(title=title).all()

    def add(self, channel: Channel) -> None:
        self.session.add(channel)

    def commit_and_close(self):
        self.session.commit()
        self.session.close()
