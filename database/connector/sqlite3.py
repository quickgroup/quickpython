"""
sqlite3 连接管理
"""
import sqlite3
import time, threading, logging
from quickpython.database.contain.func import *
from .base import Connector

log = logging.getLogger(__name__)


class Sqlite3Connector(Connector):

    engine = "sqlite3"

    def connect(self):
        """创建新连接"""
        if self.get_config('engine') == 'sqlite3':
            conn = sqlite3.connect(database=self.get_config('database'),
                                   uri=self.get_config('hostname'),
                                   isolation_level=None)
            self.connect_after(conn=conn)
            return self
        else:
            raise Exception("不支持的数据库引擎：{}".format(self.get_config('engine')))

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
