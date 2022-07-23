"""
    数据库连接管理器
"""
import pymysql
import time, threading, logging
from .. import settings
from ..contain.func import *
from .base import Connector
from ..log import get_logger
log = get_logger()


class MysqlConnector(Connector):
    engine = "mysql"

    @staticmethod
    def __load_setting(name, def_config=None):
        if def_config is not None:
            settings.DATABASES[name] = def_config
            return def_config
        if name not in settings.DATABASES:
            raise Exception("未知数据库连接配置：{}".format(name))
        return settings.DATABASES.get(name)

    def load_config(self, config2=None):
        config = {
            'name': 'default',
            'engine': "mysql",
            'hostname': "127.0.0.1",
            'port': 3306,
            'database': None,
            'username': None,
            'password': None,
            'charset': "utf8mb4",
            'wait_timeout': 3600,
            'echo': True,
            'echo_words': 1024,  # 最大字数打印
            'prefix': "",       # 表前缀
            'options': {},
        }
        if config2 is not None:
            config = {**config, **config2}
        config['port'] = int(config['port']) if not_empty(config['port']) else 3306
        config['wait_timeout'] = int(config.get('wait_timeout'))
        return config

    def connect(self):
        """创建新连接"""
        if self.get_config('engine') == 'mysql':
            conn = pymysql.connect(
                host=self.get_config('hostname'),
                port=self.get_config('port'),
                user=self.get_config('username'),
                password=self.get_config('password'),
                db=self.get_config('database'),
                charset=self.get_config('charset'))

            self.connect_after(conn=conn)
            return self

        else:
            raise Exception("不支持的数据库引擎：{}".format(self.get_config('engine')))

    def autocommit(self, x):
        self._autocommit = x
        self.__conn__().autocommit(x)     # 设置底层连接事务状态

    def get_cursor(self):
        self._check_connection_timeout()
        if self._cursor is None:
            self._cursor = self.__conn__().cursor(pymysql.cursors.DictCursor)
        return self._cursor     # type: pymysql.connect.cursorclass
