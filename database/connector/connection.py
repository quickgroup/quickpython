"""
    数据库连接管理器
"""
import os, threading
from .. import settings
from ..contain.func import *
from ..log import get_logger
log = get_logger()

# 支持的数据库引擎
from .base import Connector
from .mysql import MysqlConnector
from .sqlite3 import Sqlite3Connector


class Connection:
    # 支持的数据库引擎
    ENGINES = {
        MysqlConnector.engine: MysqlConnector,
        Sqlite3Connector.engine: Sqlite3Connector,
    }

    _local = threading.local()
    __CONFIG = {}

    @staticmethod
    def __find_config(name, def_config=None):
        if def_config is not None:
            settings.DATABASES[name] = def_config
            return def_config
        if name not in settings.DATABASES:
            raise Exception("未知数据库连接配置：{}".format(name))
        return settings.DATABASES.get(name)

    @staticmethod
    def __cache_name__(name):
        return '__{}_{}_db_{}_connection'.format(os.getpid(), get_thr_id(), name)

    @staticmethod
    def __find_engine(config) -> Connector.__class__:
        name = config.get('engine')
        if name not in Connection.ENGINES:
            raise Exception("不支持的数据库引擎：{}".format(name))
        return Connection.ENGINES.get(name)

    @staticmethod
    def connect(name=None, config=None, re_connect=False) -> Connector:
        """获取连接，已连接直接返回"""
        if name is None and config is not None and 'name' in config:
            name = config['name']
        elif empty(name):
            name = 'default'

        cache_name = Connection.__cache_name__(name)
        config = Connection.__find_config(name, config)
        obj = local_get(Connection._local, cache_name)
        if obj is None or re_connect:
            log.debug("新连接 {}".format(cache_name))
            engine = Connection.__find_engine(config)
            local_set(Connection._local, cache_name, engine(name, config=config).connect())

        return local_get(Connection._local, cache_name)
