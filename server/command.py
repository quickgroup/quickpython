"""
命令行模式
"""
import importlib, sys, logging, os, time
from quickpython.config import Config
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
            choice = sys.argv[1]
            if choice in app_cmd.COMMANDS:
                app_cmd.COMMANDS[choice](sys.argv[2:] if len(sys.argv) > 2 else [])
            else:
                logging.warning("未知命令：{}".format(choice))
        else:
            logging.warning("app/command.py脚本中未包含COMMANDS配置")


class EventManager:

    @staticmethod
    def init():
        app_path = Config.APP_PATH.replace(Config.ROOT_PATH + "/", '')
        cmd_path = str(app_path + "/event").replace("\\", ".").replace(r"/", ".")
        app_cmd = importlib.import_module(cmd_path)
