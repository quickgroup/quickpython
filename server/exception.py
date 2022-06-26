

class ResponseException(Exception):
    def __init__(self, msg=None):
        Exception.__init__(self, msg)


class ResponseRenderException(ResponseException):

    def __init__(self, tpl_name, data):
        Exception.__init__(self, tpl_name)
        self.tpl_name = tpl_name
        self.data = data


class ResponseTextException(ResponseException):

    def __init__(self, text):
        Exception.__init__(self, ResponseTextException.__name__)
        self.text = text


class ResponseNotFoundException(ResponseTextException):
    pass
