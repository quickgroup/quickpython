"""
    框架
"""
from quickpython.server.server import Core


class Boot:

    name = 'QuickPython-MVC'
    __version__ = '0.2.1'

    @classmethod
    def cmd(cls):
        Core.cmd()

    @classmethod
    def start(cls):
        Core.start()
