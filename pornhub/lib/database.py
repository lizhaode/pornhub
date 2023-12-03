import pymysql


class DataBase:
    def __init__(self, host, port, user, password):
        self.connect = pymysql.connect(
            host=host, port=port, user=user, password=password, db='pornhub', charset='utf8mb4'
        )
        self.cursor = self.connect.cursor(pymysql.cursors.DictCursor)

    def select_all_by_title_channel(self, title: str) -> tuple:
        sentence = 'SELECT * FROM `channel` WHERE `title` = %s'
        self.cursor.execute(sentence, title)
        return self.cursor.fetchall()

    def save_channel(self, title: str, channel: str, url: str, parent_url: str) -> None:
        sentence = 'INSERT INTO `channel` (`title`,`channel`,`url`,`parent_url`) VALUES(%s,%s,%s,%s)'
        self.cursor.execute(sentence, (title, channel, url, parent_url))
        self.connect.commit()

    def select_all_by_title_my_follow(self, title: str) -> tuple:
        sentence = 'SELECT * FROM `my_follow` WHERE `title` = %s'
        self.cursor.execute(sentence, title)
        return self.cursor.fetchall()

    def save_my_follow(self, title: str, channel: str, url: str, parent_url: str) -> None:
        sentence = 'INSERT INTO `my_follow` (`title`,`channel`,`url`,`parent_url`) VALUES(%s,%s,%s,%s)'
        self.cursor.execute(sentence, (title, channel, url, parent_url))
        self.connect.commit()

    def close(self):
        self.connect.close()
