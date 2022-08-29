"""
    框架
"""
from quickpython.server.server import Core


class Boot:

    name = 'QuickPython-MVC'
    __version__ = '1.0.3'

    @classmethod
    def start(cls, argv):
        Core.start(argv)

    @classmethod
    def cmd(cls, argv):
        Core.cmd(argv)

    @classmethod
    def web(cls):
        Core.web()
