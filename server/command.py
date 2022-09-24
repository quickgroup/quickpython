"""
命令行模式
"""
import importlib, sys, logging, os, time
from quickpython.config import Config
from quickpython.component import hooker
from quickpython.component.scheduler import Scheduler
from quickpython.component.scheduler import INSTALL_DPS as Scheduler_INSTALL_DPS
logger = logging.getLogger(__name__)


class CommandManager:

    @staticmethod
    def call(argv):
        try:
            CommandManager._call(argv)
        except KeyboardInterrupt as e:
            logger.info("程序退出 From KeyboardInterrupt")
        except SystemExit as e:
            logger.info("程序退出 From SystemExit")
            os._exit(0)
        except BaseException as e:
            logger.error("程序异常")
            logger.exception(e)
            time.sleep(5)

    @staticmethod
    def _call(argv):
        app_path = Config.APP_PATH.replace(Config.ROOT_PATH + "/", '')
        cmd_path = str(app_path + "/command").replace("\\", ".").replace(r"/", ".")
        app_cmd = importlib.import_module(cmd_path)
        if hasattr(app_cmd, 'COMMANDS'):
            app_cmd = app_cmd.COMMANDS
        else:
            app_cmd = {}

        # 框架自带命令
        qp_cmd = CommandManager.get_qp_cmd()
        app_cmd = {**app_cmd, **qp_cmd}

        # 执行调用
        choice = sys.argv[1]
        if choice in app_cmd:
            app_cmd[choice](sys.argv[2:] if len(sys.argv) > 2 else [])
        else:
            logging.error("未知命令：{}".format(choice))

    @staticmethod
    def get_qp_cmd():
        from quickpython.database.builder.generate import GenerateDemo
        return {
            'model_gen': GenerateDemo.call,
        }


class ComponentManager:

    @staticmethod
    def init():
        app_dir = "app"
        app_path = Config.APP_PATH.replace(Config.ROOT_PATH + "/", '')
        cmd_path = str(app_path + "/event").replace("\\", ".").replace(r"/", ".")
        app_cmd = importlib.import_module(cmd_path)
        # hooker
        hooker.start()
        # 定时器
        if Scheduler_INSTALL_DPS:
            scheduler = Scheduler.instance()
            app_crontab = importlib.import_module("{}.crontab".format(app_dir))
            if hasattr(app_crontab, 'TASKS'):
                scheduler.add(app_crontab.TASKS)

    @staticmethod
    def start():
        if Scheduler_INSTALL_DPS:
            Scheduler.instance().start()

    @staticmethod
    def app_stop():
        hooker.send(hooker.EXIT)
        hooker.stop()
        if Scheduler_INSTALL_DPS:
            Scheduler.instance().stop()
