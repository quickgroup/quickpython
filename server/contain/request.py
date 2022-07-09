
from tornado import httputil


class Request:      # type: httputil.HTTPServerRequest

    def __init__(self, target):
        super().__init__()
        self.__target = target  # type: httputil.HTTPServerRequest

    def __getattr__(self, name):
        return getattr(self.__target, name)

    def is_post(self):
        return self.__target.method == 'POST'

    def is_get(self):
        return self.__target.method == 'GET'
