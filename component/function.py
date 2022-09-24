"""
    常用方法
"""
import time

import tornado.web


def mtime():
    return int(time.time())


def action(path, header, data):
    """请求本地服务，通常用于api接口"""
    from quickpython.server.processor import ProcessorHandler
    return ProcessorHandler.action(path, header, data)
