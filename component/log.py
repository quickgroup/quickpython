"""
    日志管理
"""
import logging, datetime
from logging.handlers import TimedRotatingFileHandler
quick_name = str(__name__).split('.')[0]


class LoggingManger:

    COMPONENT = quick_name + '.component'
    DATABASE = quick_name + '.database'
    SERVER = quick_name + '.server'
    MODULES = [COMPONENT, DATABASE, SERVER]

    component = logging.getLogger(COMPONENT)
    db = logging.getLogger(DATABASE)
    server = logging.getLogger(SERVER)

    @classmethod
    def init(cls, env, log_dir, mode='WEB', debug=False):
        """初始化日志模块"""
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("matplotlib").setLevel(logging.WARNING)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
        logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
        logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)
        # 控制台
        console_handler = logging.StreamHandler()
        # 文件
        mode = mode.upper()
        encoding = env.get("encoding", "UTF-8")
        file_name = "{}_{}.log".format(mode, datetime.datetime.now().strftime("%Y-%m-%d"))
        file_path = '{}/{}'.format(log_dir, file_name)
        file_handler = TimedRotatingFileHandler(file_path, when='D', backupCount=33, encoding=encoding)
        # 全局
        format_str = '%(asctime)s %(levelname)s [%(filename)s:%(funcName)s:%(lineno)d]\t%(message)s'
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(format=format_str, level=level, handlers=[console_handler, file_handler])

    @classmethod
    def getLogger(cls, module):
        if module not in cls.MODULES:
            raise Exception("不支持的日志模块：{}".format(module))
        return logging.getLogger(module)
