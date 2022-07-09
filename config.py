import os, logging, urllib3, sys
import threading
from multiprocessing import cpu_count
from quickpython.component.env import env
from quickpython.component.logging import LoggingManger

logger = logging.getLogger(__name__)
# 屏蔽ssl警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_PATH = str(os.getcwd()).replace('\\', '/')
CACHE_PATH = ROOT_PATH + '/cache'       # cache目录
LOG_DIR = ROOT_PATH + '/cache/logs'   # 日志目录
DATA_PATH = ROOT_PATH + '/data'         # 数据目录
PUBLIC_PATH = ROOT_PATH + '/public'     # 资源目录
UPLOADS_PATH = ROOT_PATH + '/public/uploads'    # 上传目录

env.set('ROOT_PATH', ROOT_PATH)
env.set('CACHE_PATH', CACHE_PATH)
env.set('LOG_DIR', LOG_DIR)
env.set('DATA_PATH', DATA_PATH)
env.set('PUBLIC_PATH', PUBLIC_PATH)
env.set('UPLOADS_PATH', UPLOADS_PATH)


class Config:

    DEBUG = env.get("app.debug", False)
    IS_WIN32 = sys.platform == "win32"

    # 运行模式
    MODE = None     # 运行模式：web、cmd
    MODE_WEB = "WEB"
    MODE_CMD = "CMD"

    # 目录
    ROOT_PATH = ROOT_PATH
    CACHE_PATH = CACHE_PATH
    LOG_DIR = LOG_DIR
    DATA_PATH = DATA_PATH
    PUBLIC_PATH = PUBLIC_PATH
    UPLOADS_PATH = UPLOADS_PATH

    # 线程数据
    _local = threading.local()

    @classmethod
    def init(cls, mode):
        cls.MODE = str(mode).upper()
        env.set('mode', cls.MODE)
        cls.dirs_init()
        LoggingManger.init(LOG_DIR, cls.MODE, cls.DEBUG)

    @classmethod
    def dirs_init(cls):
        DIRS = [CACHE_PATH, LOG_DIR, DATA_PATH, UPLOADS_PATH]
        for it in DIRS:
            if os.path.exists(it) is False:
                logger.info('创建目录：{}'.format(it))
                os.makedirs(it)

    @staticmethod
    def get(key, default=None):
        val = env.get(key)
        if val == "true":
            val = True
        elif val == "false":
            val = False

        if val is None and default is not None:
            return default
        return val

    @staticmethod
    def env_get_int(key, default=None):
        try:
            val = env.get(key)
            return default if val is None else int(val)
        except:
            logger.error("env:{} get error".format(key))
            return default

    @classmethod
    def get_logger(cls, name):
        return logging.getLogger(name)

    @classmethod
    def web_pro_count(cls, num=None):
        return cpu_count() if num is None else num

    @classmethod
    def web_thr_count(cls, num=None):
        # thr_num = cpu_count() * 2 if num is None else num
        # thr_num = 4 if cls.is_debug() else thr_num
        return 4

    @classmethod
    def local_set(cls, name, val):
        cls._local.__setattr__(name, val)

    @classmethod
    def local_get(cls, name, def_val=None):
        if hasattr(cls._local, name):
            return cls._local.__getattribute__(name)
        return def_val
