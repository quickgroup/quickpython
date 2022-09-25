"""
    常用方法
"""
import time

import tornado.web


def mtime():
    return int(time.time())


def action(*args, **kwargs):
    """请求本地服务，通常用于api接口"""
    from quickpython.server.processor import QuickPythonHandler
    return QuickPythonHandler.action(*args, **kwargs)
