import json
import datetime, decimal


class Result:

    def __init__(self, code=200, msg="SUCCESS", data=None):
        self.code = code
        self.msg = msg
        self.data = data

    def __str__(self):
        ret = {'code': self.code, 'msg': self.msg, 'data': self.data}
        return json.dumps(ret, cls=self.JsonCustomEncoder)

    @staticmethod
    def success(data=None, msg="SUCCESS"):
        return Result.result(200, msg, data)

    @staticmethod
    def error(msg="ERROR", code=500):
        return Result.result(code, msg, None)

    @staticmethod
    def result(code, msg, data):
        return Result(code, msg, data)

    class JsonCustomEncoder(json.JSONEncoder):
        def default(self, field):
            if isinstance(field, datetime.datetime):
                return field.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(field, datetime.date):
                return field.strftime('%Y-%m-%d')
            elif isinstance(field, decimal.Decimal):
                return field.to_eng_string()
            elif hasattr(field, '__dict__'):
                return field.__dict__()
            else:
                return json.JSONEncoder.default(self, field)
