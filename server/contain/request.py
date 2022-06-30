
from tornado import httputil


class Request:      # type: httputil.HTTPServerRequest

    def __init__(self, target):
        self.target = target

    def __getattr__(self, name):
        return getattr(self.target, name)

    def is_post(self):
        return self.target.method == 'POST'

    def is_get(self):
        return self.target.method == 'GET'
