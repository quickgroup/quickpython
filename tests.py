"""
    测试
"""
import logging
import time

from libs.utils import BaseClass
from quickpython.server.processor import ProcessorController
from quickpython.boot import Boot

logger = logging.getLogger(__name__)


class Tests(BaseClass):

    def call(self, argv):
        if hasattr(self, argv[0]) is False:
            raise Exception("方法不存在：{}".format(argv[0]))
        getattr(self, argv[0], argv)()

    def test_100(self):
        """测试控制器加载"""
        ProcessorController.load_module()

        path = "index/subjoin/healthReport/index"
        controller_obj, controller_method = ProcessorController.load_controller_action(path, path.split('/'))
        logger.debug("controller_obj={}, controller_method={}".format(controller_obj, controller_method))

        path = "index/user/index"
        controller_obj, controller_method = ProcessorController.load_controller_action(path, path.split('/'))
        logger.debug("controller_obj={}, controller_method={}".format(controller_obj, controller_method))

        path = "index/signinter/xixunyun/index"
        controller_obj, controller_method = ProcessorController.load_controller_action(path, path.split('/'))
        logger.debug("controller_obj={}, controller_method={}".format(controller_obj, controller_method))

    def test_101(self):
        """读取env文件"""
        from quickpython.component.env import env

    def test_102(self):
        """测试session读写功能"""
        from quickpython.component import Session

    def boot(self):
        """测试session读写功能"""
        Boot.cmd()

    def cache(self):
        """测试cache"""
        from quickpython.component import cache
        mtime = time.time()

        cache.set('mtime', mtime, 3)
        logger.info("写入cache完成")

        data = cache.get('mtime')
        logger.info("读取cache={}".format(data))


if __name__ == "__main__":
    Test().call()

