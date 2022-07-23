"""
    数据库连接管理器
"""
import pymysql
import time, threading, logging
from .. import settings
from ..contain.func import *

from ..log import get_logger
log = get_logger()


class Connection:

    _local = threading.local()
    config = {}

    def __init__(self, name='default', config=None):
        self.name = name
        self.setting = self.__load_setting(self.name, config)
        self.load_config()
        # log.setLevel(logging.DEBUG if self.get_config('echo', True) else logging.INFO)

    @staticmethod
    def __load_setting(name, def_config=None):
        if def_config is not None:
            settings.DATABASES[name] = def_config
            return def_config
        if name not in settings.DATABASES:
            raise Exception("未知数据库连接配置")
        return settings.DATABASES.get(name)

    def load_config(self):
        cls = Connection
        if not_empty(cls.config.get(self.name)):
            return
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
            'echo_words': 256,  # 最大字数打印
            'prefix': "",       # 表前缀
            'options': {},
        }
        config = {**config, **self.setting}
        config['port'] = int(config['port']) if not_empty(config['port']) else 3306
        config['wait_timeout'] = int(config['wait_timeout'])
        cls.config[self.name] = config
        log.setLevel(logging.DEBUG if config.get('echo', True) else logging.INFO)

    def get_config(self, key, def_val=None):
        config = self.config.get(self.name)
        if key in config:
            return config[key]
        if key in config['options']:
            return config['options'][key]
        return def_val

    def __local_key__(self, before=''):
        return '__db_{}_connection_{}'.format(self.name, before)

    @staticmethod
    def __get_obj__(name):
        key_name = '__db_' + name
        obj = local_get(Connection._local, key_name)
        if obj is None:
            local_set(Connection._local, key_name, Connection(name))
        return local_get(Connection._local, key_name)   # type: Connection

    @staticmethod
    def connect(name='default', re_connect=False):
        """获取连接，已连接直接返回"""
        obj = Connection.__get_obj__(name)
        connect = local_get(Connection._local, obj.__local_key__())
        if connect is None or re_connect:
            local_set(Connection._local, obj.__local_key__(), obj._connect(obj))

        return obj       # 返回本类，实现方法直接调用

    def __conn__(self):
        """获取连接"""
        self.connect(self.name)
        return local_get(Connection._local, self.__local_key__())  # 真实的pymysql连接

    @staticmethod
    def _connect(obj: "Connection"):
        """创建新连接"""
        local_set(Connection._local, obj.__local_key__(), None)
        local_set(Connection._local, obj.__local_key__('_curr'), None)
        if obj.get_config('engine') == 'mysql':
            conn = pymysql.connect(
                host=obj.get_config('hostname'),
                port=obj.get_config('port'),
                user=obj.get_config('username'),
                password=obj.get_config('password'),
                db=obj.get_config('database'),
                charset=obj.get_config('charset'))

            conn.autocommit(True)
            conn.__thr_id = get_thr_id()
            conn.__in_transaction = False   # 非事务中
            conn.__expire_time = int(time.time()) + obj.get_config('wait_timeout')  # 超时时间
            return conn

        else:
            raise Exception("不支持的数据库引擎：{}".format(obj.get_config('engine')))

    def get_cursor(self):
        self._check_connection_timeout()
        name = self.get_config('name')
        curr = local_get(Connection._local, self.__local_key__('_curr'))
        if curr is None:
            curr = self.__conn__().cursor(pymysql.cursors.DictCursor)
            local_set(Connection._local, self.__local_key__('_curr'), curr)

        return curr     # type: pymysql.connect.cursorclass

    def _check_connection_timeout(self):
        """检测超时，超时将重新连接（处于事务中时不重连）"""
        conn = self.__conn__()
        if conn.autocommit_mode is False:       # 事务中跳过，非自动提交就是在事务中
            return
        if conn.__expire_time <= int(time.time()):
            self.connect(self.name, re_connect=True)

    def ping(self):
        """数据库PING"""

    def start_trans(self):
        """开启事务"""
        log.debug("start_trans")
        self._check_connection_timeout()     # TODO::获取游标时检测超时
        self.__conn__().autocommit(False)    # 关闭自动提交

    def commit(self):
        """提交事务"""
        log.debug("commit")
        conn = self.__conn__()
        conn.commit()
        conn.autocommit(True)

    def rollback(self):
        """回滚事务"""
        log.debug("rollback")
        conn = self.__conn__()
        conn.rollback()
        conn.autocommit(True)

    def _cur_execute(self, cur, sql):
        try:
            log.debug(self.get_config('engine') + ": " + (sql if len(sql) <= 1024 else sql[0:1024]))
            return cur.execute(sql)

        except SystemExit as e:
            self.close()
            raise e
        except BaseException as e:
            log.exception("SQL: {}".format(sql))
            raise e

    def execute(self, sql):
        cur = self.get_cursor()
        # count = cur.execute(sql)
        count = self._cur_execute(cur, sql)
        row = cur.fetchone()
        return count, row, cur.description

    def execute_all(self, sql):
        cur = self.get_cursor()
        # count = cur.execute(sql)
        count = self._cur_execute(cur, sql)
        rows = cur.fetchall()
        return count, rows, cur.description

    def execute_get_id(self, sql):
        conn = self.__conn__()
        cur = self.get_cursor()
        # count = cur.execute(sql)
        count = self._cur_execute(cur, sql)
        row = cur.fetchone()
        return count, row, conn.insert_id()

    def execute_find(self, sql):
        return self.execute(sql)[1]

    def close(self):
        self.get_cursor().close()
        self.__conn__().close()
