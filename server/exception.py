

class AppException(Exception):
    pass


class ResponseException(AppException):
    def __init__(self, msg, url=None, data=None, wait=None, code=302):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.url = url
        self.data = data
        self.wait = 3 if wait is None else wait

    def __str__(self):
        return str(self.msg)

    def __dict__(self):
        return {'code': self.code, 'msg': self.msg,
                'url': self.url, 'data': self.data, 'wait': self.wait}


class ResponseFileException(AppException):
    def __init__(self, file, mime=None):
        self.file = file
        self.mime = mime


class ResponseRenderException(ResponseException):
    def __init__(self, tpl_name, data, code=200):
        super().__init__(tpl_name, code)
        self.tpl_name = tpl_name
        self.data = data


class ResponseTextException(ResponseException):
    def __init__(self, text, code=200):
        super().__init__(text, code=code)
        self.text = text


class ResponseNotFoundException(ResponseTextException):
    def __init__(self, text):
        super().__init__(text, code=404)
