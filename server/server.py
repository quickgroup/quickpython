import sys, signal, logging, datetime
import tornado.ioloop
import tornado.web
from quickpython.config import Config
from .settings import SETTINGS, ROUTES


class Core:
    log = logging.getLogger(__name__)

    @classmethod
    def signal_init(cls):
        """监听退出"""

        def signin_exit(signum, frame):
            # cls.log.info("进程停止")
            tornado.ioloop.IOLoop.instance().stop()
            cls.log.info("进程停止 完成")

        # signal.signal(signal.SIGQUIT, signin_exit)
        signal.signal(signal.SIGTERM, signin_exit)
        signal.signal(signal.SIGINT, signin_exit)

        # tornado专属停止方式
        def set_ping(ioloop, timeout):
            ioloop.add_timeout(timeout, lambda: set_ping(ioloop, timeout))

        set_ping(tornado.ioloop.IOLoop.instance(), datetime.timedelta(seconds=1))

    @classmethod
    def init(cls, mode):
        Config.init(mode)
        cls.signal_init()
        logging.getLogger("tornado.access").setLevel(logging.ERROR)

    @classmethod
    def cmd(cls):
        cls.init(Config.MODE_CMD)
        cls.log.info("##########   Command mode   ##########")

    @classmethod
    def start(cls):
        """启动web环境"""
        cls.init(Config.MODE_WEB)
        # 配置
        application = tornado.web.Application(ROUTES, **{
            'template_path': SETTINGS['template_path'],
            'ui_methods': SETTINGS['ui_methods'],
        })  # , debug=SETTINGS['debug'])
        # 启动web
        server = cls.server = tornado.web.HTTPServer(application, decompress_request=True)
        if Config.IS_WIN32:
            server.listen(SETTINGS['port'])
        else:
            server.bind(SETTINGS['port'])
            server.start(0)     # 当参数小于等于０时，则根据当前机器的cpu核数来创建子进程，大于１时直接根据指定参数创建子进程

        cls.log.info("WEB start complete, port={}".format(SETTINGS['port']))
        tornado.ioloop.IOLoop.instance().start()
        # 关闭
        # tornado.ioloop.IOLoop.current().stop()


if __name__ == "__main__":
    Core.start()
