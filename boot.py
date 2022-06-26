"""
    框架
"""
from quickpython.server.server import Core


class Boot:

    @classmethod
    def cmd(cls):
        Core.cmd()

    @classmethod
    def start(cls):
        Core.start()
