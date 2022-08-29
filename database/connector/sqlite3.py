"""
sqlite3 连接管理
"""
import sqlite3
import logging
from .base import Connector

log = logging.getLogger(__name__)


class Sqlite3Connector(Connector):
    engine = "sqlite3"

    def _connect(self):
        """创建新连接"""
        conn = sqlite3.connect(database=self.get_config('database'),
                               uri=self.get_config('uri', None),
                               isolation_level=None)
        conn.execute("PRAGMA synchronous=OFF")   # 关闭同步
        conn.row_factory = Sqlite3Connector.dict_factory
        return conn

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def _autocommit(self, x):
        if self._autocommit:
            self.execute("BEGIN;")

    def _get_cursor(self):
        return self.__conn__().cursor()
