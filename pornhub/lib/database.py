import pymysql

HOST = ''
PORT = 3306
USER = 'root'
PASSWORD = ''


class DataBase:

    def __init__(self):
        self.connect = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, db='pornhub',
                                       charset='utf8mb4')
        self.cursor = self.connect.cursor(pymysql.cursors.DictCursor)

    def select_all_by_title(self, title: str) -> tuple:
        sentence = 'SELECT * FROM `channel` WHERE `title` = %s'
        self.cursor.execute(sentence, title)
        return self.cursor.fetchall()

    def save(self, title: str, channel: str, url: str, parent_url: str) -> None:
        sentence = 'INSERT INTO `channel` (`title`,`channel`,`url`,`parent_url`) VALUES(%s,%s,%s,%s)'
        self.cursor.execute(sentence, (title, channel, url, parent_url))
        self.connect.commit()

    def close(self):
        self.connect.close()
