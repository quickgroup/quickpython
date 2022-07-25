import sys, signal, logging, datetime
import tornado.ioloop
import tornado.web
from config import Config       # 应用需要自己有一个config文件，或者包含且继承quickpython.config
from quickpython.component import hooker
from .settings import SETTINGS, ROUTES
from .command import CommandManager, EventManager


class Core:
    log = logging.getLogger(__name__)

    @classmethod
    def _web_signal_init(cls):
        """web环境监听退出，不能再bind之前调用"""

        def signin_exit(signum, frame):
            cls.log.debug("进程停止")
            tornado.ioloop.IOLoop.instance().stop()
            cls._app_stop()
            cls.log.info("进程停止 完成")

        # signal.signal(signal.SIGQUIT, signin_exit)
        signal.signal(signal.SIGTERM, signin_exit)
        signal.signal(signal.SIGINT, signin_exit)

        # tornado专属停止方式
        def set_ping(ioloop, timeout):
            ioloop.add_timeout(timeout, lambda: set_ping(ioloop, timeout))

        set_ping(tornado.ioloop.IOLoop.instance(), datetime.timedelta(seconds=1))

    @classmethod
    def _cmd_signal_init(cls):
        """cmd模型信号处理"""
        def my_handler(signum, frame):              # 信号处理函数
            cls.log.debug("App stop")
            cls._app_stop()
            cls.log.info("App stop complete.")

        signal.signal(signal.SIGINT, my_handler)    # 设置相应信号处理的handler
        # signal.signal(signal.SIGHUP, my_handler)
        signal.signal(signal.SIGTERM, my_handler)

    @classmethod
    def _app_stop(cls):
        hooker.send(hooker.EXIT)
        hooker.stop()

    @classmethod
    def start(cls, argv):
        mode = argv[0] if len(argv) > 0 else None
        if mode == "cmd":
            cls.cmd(argv)
        elif mode == "web":
            cls.web()
        else:
            raise Exception("缺少启动模式参数")

    @classmethod
    def init(cls, mode):
        Config.init(mode)
        hooker.start()
        EventManager.init()
        logging.getLogger("tornado.access").setLevel(logging.ERROR)

    @classmethod
    def cmd(cls, argv):
        """cmd环境"""
        cls.init(Config.MODE_CMD)
        cls._cmd_signal_init()
        cls.log.info("App cmd start")
        # 加载命令行程序
        CommandManager.call(argv)
        # 应用结束
        hooker.send(hooker.EXIT)
        hooker.stop()

    @classmethod
    def web(cls):
        """启动web环境"""
        cls.init(Config.MODE_WEB)
        # 配置
        settings = {
            # 'debug': SETTINGS['debug'],
        }
        # 实例化应用
        application = tornado.web.Application(ROUTES, **{
            'template_path': SETTINGS['template_path'],
            'ui_methods': SETTINGS['ui_methods'],
        }, **settings)
        # 启动web
        server = cls.server = tornado.web.HTTPServer(application, decompress_request=True)
        if Config.IS_WIN32:
            server.listen(SETTINGS['port'])
        else:
            server.bind(SETTINGS['port'])
            server.start(0)     # 当参数小于等于０时，则根据当前机器的cpu核数来创建子进程，大于１时直接根据指定参数创建子进程

        cls._web_signal_init()
        cls.log.info("WEB start complete, port={}".format(SETTINGS['port']))
        tornado.ioloop.IOLoop.instance().start()
        # 关闭
        # tornado.ioloop.IOLoop.current().stop()


if __name__ == "__main__":
    Core.start()
