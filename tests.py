"""
    测试
"""
import logging
from libs.utils import BaseClass
from quickpython.server.processor import ProcessorController
from quickpython.boot import Boot

logger = logging.getLogger(__name__)


class Test(BaseClass):

    def call(self, *args):
        self.test_102()

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
        from quickpython.component.session import Session

    def boot(self):
        """测试session读写功能"""
        Boot.cmd()


if __name__ == "__main__":
    Test().call()

