"""
    数据库连接管理器
"""
import abc, logging
from ..contain.func import *

from ..log import get_logger
log = get_logger()


class ConnectProxy:
    """数据库连接代理对象，方便增加兼容方法，比如：事务控制、超时配置等"""


class Connector:
    engine = None
    __COMMON_CONFIG = {
        'name': 'default',
        'engine': None,
        'hostname': None,
        'port': None,
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

    def __init__(self, name='default', config=None):
        self.name = name
        self.config = self.load_config(config)
        self.log = log
        self.__conn = None      # 数据库连接，子类不能直接访问
        self._cursor = None    # 连接游标
        self._thr_id = get_thr_id()
        self._autocommit_of = True   # 自动提交（False表示在事务中
        self._expire_time = int(time.time()) + self.get_config('wait_timeout')  # 超时时间
        log.setLevel(logging.DEBUG if self.config.get('echo', True) else logging.INFO)

    def load_config(self, config2=None):
        config = self.__COMMON_CONFIG
        if config2 is not None:
            config = {**config, **config2}
        return config

    def get_config(self, key, def_val=None):
        if key in self.config:
            return self.config[key]
        if 'options' in self.config and key in self.config['options']:
            return self.config['options'][key]
        return def_val

    def connect(self):
        self.connect_before()
        conn = self._connect()
        self.connect_after(conn=conn)
        return self

    @abc.abstractmethod
    def _connect(self):
        """子类实现具体连接方法"""

    def connect_before(self):
        self.__conn = None
        self._cursor = None

    def connect_after(self, conn):
        """连接成功后设置环境"""
        self.__conn = conn      # 数据库连接
        self._cursor = None    # 连接游标
        self._thr_id = get_thr_id()
        self.autocommit(True)
        self._expire_time = int(time.time()) + self.get_config('wait_timeout')  # 超时时间

    def __conn__(self):
        self._check_connection_timeout()
        return self.__conn

    def get_cursor(self):
        self._check_connection_timeout()
        if self._cursor is None:
            self._cursor = self._get_cursor()
        return self._cursor

    @abc.abstractmethod
    def _get_cursor(self):
        """获取游标：子类实现具体连接方法"""

    def _check_connection_timeout(self):
        """检测超时，超时将重新连接（处于事务中时不重连）"""
        if self._autocommit_of is False:  # 事务中不检测
            return
        if self._expire_time <= int(time.time()):  # 超时调用重连
            self.connect()

    def ping(self):
        """数据库PING"""

    def on_echo(self, x):
        self.config['echo'] = x
        self.log.setLevel(logging.DEBUG if x else logging.INFO)

    def autocommit(self, x):
        self._autocommit_of = x
        self._autocommit(x)

    @abc.abstractmethod
    def _autocommit(self, x):
        """开启事务"""

    def is_autocommit(self):
        return self._autocommit_of

    def start_trans(self):
        """开启事务"""
        log.debug("start_trans")
        self._check_connection_timeout()     # TODO::获取游标时检测超时
        self.autocommit(False)

    def commit(self):
        """提交事务"""
        log.debug("commit")
        self.__conn.commit()
        self.autocommit(True)

    def rollback(self):
        """回滚事务"""
        log.debug("rollback")
        self.__conn.rollback()
        self.autocommit(True)

    def _cur_execute(self, cur, sql: str):
        try:
            sql = sql.strip()
            # log.debug(self.get_config('engine') + ": " + (sql if len(sql) <= 1024 else sql[0:1024]))
            log.debug((sql if len(sql) <= 1024 else sql[0:1024]))
            return cur.execute(sql)

        except SystemExit as e:
            self.close()
            raise e
        except BaseException as e:
            log.exception("{}({}){} Exception SQL:{}".format(self.name, self.get_config('engine'), self.__conn, sql))
            raise e

    def execute(self, sql):
        cur = self.get_cursor()
        count = self._cur_execute(cur, sql)
        row = cur.fetchone()
        return count, row, cur.description

    def execute_all(self, sql):
        cur = self.get_cursor()
        count = self._cur_execute(cur, sql)
        rows = cur.fetchall()
        return count, rows, cur.description

    def execute_get_id(self, sql):
        cur = self.get_cursor()
        count = self._cur_execute(cur, sql)
        row = cur.fetchone()
        return count, row, self.__conn__().insert_id()

    def execute_find(self, sql):
        return self.execute(sql)[1]

    def close(self):
        self.get_cursor().close()
        self.__conn.close()
