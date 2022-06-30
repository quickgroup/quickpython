

class AppException(Exception):
    pass


class ResponseException(AppException):
    def __init__(self, text, status_code=200):
        super().__init__(text)
        self.text = text
        self.status_code = status_code


class ResponseFileException(AppException):
    def __init__(self, file, mime=None):
        self.file = file
        self.mime = mime


class RedirectException(ResponseException):
    def __init__(self, url, status_code=302):
        super().__init__(url, status_code)
        self.url = url


class ResponseRenderException(ResponseException):
    def __init__(self, tpl_name, data, status_code=200):
        super().__init__(tpl_name, status_code)
        self.tpl_name = tpl_name
        self.data = data


class ResponseTextException(ResponseException):
    def __init__(self, text, status_code=200):
        super().__init__(text, status_code)
        self.text = text


class ResponseNotFoundException(ResponseTextException):
    pass
