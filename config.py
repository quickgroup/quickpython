import os, logging, urllib3, sys
import threading
from multiprocessing import cpu_count
from quickpython.component.env import env
from quickpython.component.log import LoggingManger

logger = logging.getLogger(__name__)
# 屏蔽ssl警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_PATH = str(os.getcwd()).replace('\\', '/')
APP_PATH = str(os.getcwd()).replace('\\', '/') + '/app'
CACHE_PATH = ROOT_PATH + '/cache'       # cache目录
LOG_DIR = ROOT_PATH + '/cache/logs'   # 日志目录
DATA_PATH = ROOT_PATH + '/data'         # 数据目录
PUBLIC_PATH = ROOT_PATH + '/public'     # 资源目录
UPLOADS_PATH = ROOT_PATH + '/public/uploads'    # 上传目录

env.set('ROOT_PATH', ROOT_PATH)
env.set('APP_PATH', APP_PATH)
env.set('CACHE_PATH', CACHE_PATH)
env.set('LOG_DIR', LOG_DIR)
env.set('DATA_PATH', DATA_PATH)
env.set('PUBLIC_PATH', PUBLIC_PATH)
env.set('UPLOADS_PATH', UPLOADS_PATH)


class Config:

    DEBUG = env.get("app.debug", False)
    IS_WIN32 = sys.platform == "win32"

    # 运行模式
    MODE = None
    MODE_WEB = "WEB"
    MODE_CMD = "CMD"

    # 目录
    ROOT_PATH = ROOT_PATH
    APP_PATH = APP_PATH
    CACHE_PATH = CACHE_PATH
    LOG_DIR = LOG_DIR
    DATA_PATH = DATA_PATH
    PUBLIC_PATH = PUBLIC_PATH
    UPLOADS_PATH = UPLOADS_PATH

    # app配置
    SETTINGS = {
        'debug': env.get('app.debug', False),
        'port': env.get('app.port', 32000),
        'version': '0.2.1',
        'template_path': 'app',
        'public_path': 'public',
        'static_path': 'public/static',
        'pro_thr_num': None,  # 默认是CPU核心数的线程数量
        # 环境配置
        'lang': 'zh-cn',
        'timezone': 'PRC',
        'encoding': 'utf-8',  # 全局框架文件默认编码
        # 应用设置
        'default_module': 'index',
        'default_controller': 'index',
        'default_action': 'index',
        'url_convert': True,  # 自动转换为控制器方法
        'url_route_on': False,
        'url_html': '.html',
        # 模板配置
        'template': {
            'view_path': '',
            'view_suffix': 'html',
            'cache': True,
        },
        'view_replace_str': {
            '__PUBLIC__': '',
            '__ROOT__': '',
            '__CDN__': '',
        },
        'dispatch_success_tmpl': "",
        'dispatch_error_tmpl': "",
        'dispatch_exception_tmpl': "",
        'error_message': "你所浏览的页面暂时无法访问",
        'exception_handle': '',
        # 验证码
        'captcha': {
            'code_set': '2345678abcdefhijkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXY',
            'font_size': 18,
            'height': 40,
            'width': 130,
            'count': 5,
        },
        #
        'resource_max_age': 86400,
    }

    # 缓存设置
    CACHE = {
        'type': "memory",  # 缓存类型：memory=内存、file=文件、redis=redis方式
        'timeout': 1800,  # 默认过期时间
    }

    # session配置
    SESSIONS = {
        'prefix': 'qp_',
        'type': "",
        'expire': 86400 * 7,
    }

    # 日志配置
    LOGGING = {
        'default': {
            'level': 'DEBUG',
        }
    }

    # 线程数据
    _local = threading.local()

    @classmethod
    def init(cls, mode):
        """cls上的属性可以被子类覆盖，直接调用父类不会覆盖"""
        cls.MODE = str(mode).upper()
        env.set('mode', cls.MODE)
        # 主要配置
        for key in cls.SETTINGS:
            env.set(key, cls.SETTINGS.get(key))
        # 目录初始化
        DIRS = [CACHE_PATH, LOG_DIR, DATA_PATH, UPLOADS_PATH]
        for it in DIRS:
            if os.path.exists(it) is False:
                os.makedirs(it)
        # 日志初始化
        LoggingManger.init(env, LOG_DIR, cls.MODE, cls.DEBUG)

    @staticmethod
    def get(key, def_val=None):
        return env.get(key, def_val)

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
        return 8

    @classmethod
    def local_set(cls, name, val):
        cls._local.__setattr__(name, val)

    @classmethod
    def local_get(cls, name, def_val=None):
        if hasattr(cls._local, name):
            return cls._local.__getattribute__(name)
        return def_val
