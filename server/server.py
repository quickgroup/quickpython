import sys, signal, logging, datetime
import tornado.ioloop
import tornado.web
from quickpython.component import hooker
from .command import CommandManager, EventManager
from quickpython.server import Config


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

        def my_handler(signum, frame):  # 信号处理函数
            cls._app_stop()
            import os
            os._exit(0)

        signal.signal(signal.SIGINT, my_handler)  # 设置相应信号处理的handler
        # signal.signal(signal.SIGHUP, my_handler)
        signal.signal(signal.SIGTERM, my_handler)

    @classmethod
    def _app_stop(cls):
        cls.log.debug("App stop")
        hooker.send(hooker.EXIT)
        hooker.stop()
        cls.log.info("App stop complete.")

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
        cls.log.info("App cmd start, argv={}".format(argv))
        CommandManager.call(argv)       # 命令行处理
        cls._app_stop()     # 应用结束

    @classmethod
    def web(cls):
        """启动web环境"""
        cls.init(Config.MODE_WEB)
        # 配置
        settings = {
            # 'debug': SETTINGS['debug'],
        }
        # 常用方法
        import quickpython.component.function as functions
        SETTINGS = Config.SETTINGS
        # 路由
        from .processor import ProcessorHandler
        ROUTES = [
            (r"/(.*)", ProcessorHandler),  # 默认处理控制器
        ]
        try:
            from app.route import ROUTES as APP_ROUTES
            ROUTES.extend(APP_ROUTES)
        except:
            pass
        # 实例化应用
        application = tornado.web.Application(ROUTES, **{
            'template_path': SETTINGS['template_path'],
            'ui_methods': functions,
        }, **settings)
        # 启动web
        server = cls.server = tornado.web.HTTPServer(application, decompress_request=True)
        mode = 2  # 2=全平台统一多线程，1=linux多进程，win多线程
        if mode == 1:
            if Config.IS_WIN32:
                server.listen(SETTINGS['port'])
            else:
                server.bind(SETTINGS['port'])
                server.start(0)  # 当参数小于等于０时，则根据当前机器的cpu核数来创建子进程，大于１时直接根据指定参数创建子进程
        else:
            server.listen(SETTINGS['port'])

        cls._web_signal_init()
        cls.log.info("WEB start complete, port={}".format(SETTINGS['port']))
        tornado.ioloop.IOLoop.instance().start()
        # 关闭
        # tornado.ioloop.IOLoop.current().stop()


if __name__ == "__main__":
    Core.start()
