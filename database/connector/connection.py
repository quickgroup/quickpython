"""
    数据库连接管理器
"""
import pymysql
import time, threading, logging
from .. import setttings
from ..contain.func import *
log = logging.getLogger(__name__)

thr_id_dict = {}


class Connection:

    _local = threading.local()

    def __init__(self):
        self._is_trans_ing = False
        self._conn = None
        self._conn_start_time = int(time.time())
        self.config = {
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
        self.config = {**self.config, **setttings.DATABASES['default']}
        self.config['port'] = int(self.config['port']) if not_empty(self.config['port']) else 3306
        self.config['wait_timeout'] = int(self.config['wait_timeout'])
        log.setLevel(logging.DEBUG if self.get_config('echo', True) else logging.INFO)

    def get_config(self, name, def_val=None):
        if name in self.config:
            return self.config[name]
        return self.config['options'][name] if name in self.config['options'] else def_val

    @staticmethod
    def connect(re_connect=False):
        """获取连接，已连接将返回"""
        connect = local_get(Connection._local, '__db_connection')
        if connect is not None and re_connect is False:
            return connect

        connection = Connection()
        connection._connect()
        local_set(Connection._local, '__db_connection', connection)
        return connection

    def _connect(self):
        """创建新连接"""
        local_set(Connection._local, '__db_connection', None)
        if self.config['engine'] == 'mysql':
            self._conn = pymysql.connect(
                host=self.config['hostname'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                db=self.config['database'],
                charset=self.config['charset'])

            self._conn.autocommit(True)

        else:
            raise Exception("不支持的数据库引擎：{}".format(self.config['engine']))

        self._conn_start_time = int(time.time())
        return self

    def get_cursor(self):
        self._check_connection_timeout()
        curr = local_get(Connection._local, '__db_connection_curr')
        if curr is None:
            curr = self._conn.cursor(pymysql.cursors.DictCursor)
            local_set(Connection._local, '__db_connection_curr', curr)

        return curr

    def _check_connection_timeout(self):
        """检测超时，超时将重新连接（处于事务中时不会重连）"""
        if self._is_trans_ing:      # 事务中不检测
            return False
        curr_time = int(time.time())
        if curr_time - self._conn_start_time >= self.config['wait_timeout']:
            self.connect(True)

    def ping(self):
        """数据库PING"""

    def start_trans(self):
        """开启事务"""
        self._check_connection_timeout()       # TODO::获取游标时检测超时
        log.debug("start_trans")
        self._conn.autocommit(False)

    def commit(self):
        """提交事务"""
        log.debug("commit")
        self._conn.commit()
        self._conn.autocommit(True)

    def rollback(self):
        """回滚事务"""
        log.debug("rollback")
        self._conn.rollback()
        self._conn.autocommit(True)

    def execute(self, sql):
        log.debug(sql)
        cur = self.get_cursor()
        count = cur.execute(sql)
        ret = cur.fetchone()
        return count, ret, cur.description

    def execute_all(self, sql):
        log.debug(sql)
        cur = self.get_cursor()
        log.info("thd={}, conn={}, cursor={}, \nsql={}"
                 .format(threading.current_thread().ident, self.connect()._conn, self.get_cursor(), sql))
        count = cur.execute(sql)
        ret = cur.fetchall()
        return count, ret, cur.description

    def execute_get_id(self, sql):
        log.debug(sql)
        cur = self.get_cursor()
        count = cur.execute(sql)
        ret = cur.fetchone()
        ret_id = self._conn.insert_id()
        return count, ret, ret_id

    def execute_find(self, sql):
        count, ret, _ = self.execute(sql)
        return ret

    def close(self):
        self._conn.close()
