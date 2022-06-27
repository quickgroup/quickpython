import json


class Result:

    def __init__(self, code=200, msg="SUCCESS", data=None):
        self.code = code
        self.msg = msg
        self.data = data

    def __str__(self):
        ret = {'code': self.code, 'msg': self.msg, 'data': self.data}
        return json.dumps(ret, indent=99)

    @staticmethod
    def success(data=None, msg="SUCCESS"):
        return Result.result(200, msg, data)

    @staticmethod
    def error(msg="ERROR", code=500):
        return Result.result(code, msg, None)

    @staticmethod
    def result(code, msg, data):
        return Result(code, msg, data)
