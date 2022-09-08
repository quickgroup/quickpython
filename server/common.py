"""
    统一引入框架
"""

from quickpython.config import Config, env

try:
    import tornado
    from tornado import web, httputil
    from tornado.concurrent import run_on_executor
except:
    pass
