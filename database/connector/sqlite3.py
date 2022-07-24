"""
sqlite3 连接管理
"""
import sqlite3
import logging
from .base import Connector

log = logging.getLogger(__name__)


class Sqlite3Connector(Connector):

    engine = "sqlite3"

    def connect(self):
        """创建新连接"""
        if self.get_config('engine') == 'sqlite3':
            conn = sqlite3.connect(database=self.get_config('database'),
                                   uri=self.get_config('uri', None),
                                   isolation_level=None)
            conn.execute("PRAGMA synchronous=OFF")   # 关闭同步
            conn.row_factory = Sqlite3Connector.dict_factory
            self.connect_after(conn=conn)
            return self
        else:
            raise Exception("不支持的数据库引擎：{}".format(self.get_config('engine')))

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def autocommit(self, x):
        self._autocommit = x
        if self._autocommit:
            self.execute("BEGIN;")

    def get_cursor(self):
        self._check_connection_timeout()
        if self._cursor is None:
            self._cursor = self.__conn__().cursor()
        return self._cursor

    # def sync_db(self, is_open=True):
    #     self._sync_db = is_open
