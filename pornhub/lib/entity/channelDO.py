from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime

Base = declarative_base()


class Channel(Base):

    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    channel = Column(String)
    url = Column(String)
    parent_url = Column(String)
    create_timestamp = Column(DateTime)
    update_timestamp = Column(DateTime)

    def __repr__(self):
        return 'Channel[id={0}, title={1}, channel={2}, url={3}, parent_url={4}, create_timestamp={5}, ' \
               'update_timestamp={6}]'.format(self.id, self.title, self.channel, self.url, self.parent_url,
                                              self.create_timestamp, self.update_timestamp)
