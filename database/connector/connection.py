"""
    数据库连接管理器
"""
import pymysql
import time, threading, logging
from .. import setttings
from ..contain.func import *

from ..log import get_logger
log = get_logger()


class Connection:

    _local = threading.local()
    config = {}

    def __init__(self):
        self.load_config()
        # log.setLevel(logging.DEBUG if self.get_config('echo', True) else logging.INFO)

    @classmethod
    def load_config(cls):
        if not_empty(cls.config):
            return
        cls.config = {
            'engine': "mysql",
            'hostname': "127.0.0.1",
            'port': 3306,
            'database': None,
            'username': None,
            'password': None,
            'charset': "utf8mb4",
            'wait_timeout': 3600,
            'prefix': "",       # 表前缀
            'options': {},
        }
        cls.config = {**cls.config, **setttings.DATABASES['default']}
        cls.config['port'] = int(cls.config['port']) if not_empty(cls.config['port']) else 3306
        cls.config['wait_timeout'] = int(cls.config['wait_timeout'])
        log.setLevel(logging.DEBUG if cls.config.get('echo', True) else logging.INFO)

    @staticmethod
    def get_config(name, def_val=None):
        cls = Connection
        cls.load_config()
        if name in cls.config:
            return cls.config[name]
        if name in cls.config['options']:
            return cls.config['options'][name]
        return def_val

    @staticmethod
    def connect(re_connect=False):
        """获取连接，已连接直接返回"""
        connect = local_get(Connection._local, '__db_pm_connection')
        if connect is None or re_connect:
            local_set(Connection._local, '__db_pm_connection', Connection._connect())

        return Connection       # 返回本类，实现方法直接调用

    @classmethod
    def __conn__(cls):
        cls.connect()
        return local_get(Connection._local, '__db_pm_connection')  # 真实的pymysql连接

    @classmethod
    def _connect(cls):
        """创建新连接"""
        local_set(Connection._local, '__db_pm_connection', None)
        local_set(Connection._local, '__db_pm_connection_curr', None)
        if cls.get_config('engine') == 'mysql':
            conn = pymysql.connect(
                host=cls.get_config('hostname'),
                port=cls.get_config('port'),
                user=cls.get_config('username'),
                password=cls.get_config('password'),
                db=cls.get_config('database'),
                charset=cls.get_config('charset'))

            conn.autocommit(True)
            conn.__thr_id = get_thr_id()
            conn.__in_transaction = False   # 非事务中
            conn.__conn_start_time = int(time.time())   # 连接时间
            return conn

        else:
            raise Exception("不支持的数据库引擎：{}".format(cls.get_config('engine')))

    @classmethod
    def get_cursor(cls):
        cls._check_connection_timeout()
        curr = local_get(Connection._local, '__db_pm_connection_curr')
        if curr is None:
            curr = cls.__conn__().cursor(pymysql.cursors.DictCursor)
            local_set(Connection._local, '__db_pm_connection_curr', curr)

        return curr     # type: pymysql.connect.cursorclass

    @classmethod
    def _check_connection_timeout(cls):
        """检测超时，超时将重新连接（处于事务中时不会重连）"""
        conn = cls.__conn__()
        if conn.autocommit_mode:       # 事务中跳过
            return False
        curr_time = int(time.time())
        if curr_time - conn.__conn_start_time >= cls.get_config('wait_timeout'):
            cls.connect(True)

    def ping(self):
        """数据库PING"""

    @classmethod
    def start_trans(cls):
        """开启事务"""
        log.debug("start_trans")
        cls._check_connection_timeout()       # TODO::获取游标时检测超时
        cls.__conn__().autocommit(False)

    @classmethod
    def commit(cls):
        """提交事务"""
        log.debug("commit")
        conn = cls.__conn__()
        conn.commit()
        conn.autocommit(True)

    @classmethod
    def rollback(cls):
        """回滚事务"""
        log.debug("rollback")
        conn = cls.__conn__()
        conn.rollback()
        conn.autocommit(True)

    @classmethod
    def __cur_execute__(cls, cur, sql):
        try:
            log.debug(sql)
            return cur.execute(sql)

        except SystemExit as e:
            cls.close()
            raise e
        except BaseException as e:
            log.exception("SQL: {}".format(sql))
            raise e

    @classmethod
    def execute(cls, sql):
        conn = cls.__conn__()
        cur = cls.get_cursor()
        # count = cur.execute(sql)
        count = cls.__cur_execute__(cur, sql)
        ret = cur.fetchone()
        return count, ret, cur.description

    @classmethod
    def execute_all(cls, sql):
        conn = cls.__conn__()
        cur = cls.get_cursor()
        # count = cur.execute(sql)
        count = cls.__cur_execute__(cur, sql)
        ret = cur.fetchall()
        return count, ret, cur.description

    @classmethod
    def execute_get_id(cls, sql):
        conn = cls.__conn__()
        cur = cls.get_cursor()
        # count = cur.execute(sql)
        count = cls.__cur_execute__(cur, sql)
        ret = cur.fetchone()
        ret_id = conn.insert_id()
        return count, ret, ret_id

    @classmethod
    def execute_find(cls, sql):
        return cls.execute(sql)[1]

    @classmethod
    def close(cls):
        cls.get_cursor().close()
        cls.__conn__().close()
