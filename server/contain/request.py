
import logging, json
from ..common import *

logger = logging.getLogger(__name__)


class Request:

    def __init__(self):
        self.status = 200
        self.headers = {}
        self.cookies = {}
        self.method = None
        self.path = None
        self.remote_ip = None
        self.query_arguments = None
        self.arguments = None
        self.__target = None

    def __load_from_tornado__(self, req, hdl):
        """从tornado加载请求信息"""
        self.__target = req
        self.status = hdl.get_status()
        self.remote_ip = req.remote_ip
        # 路径处理
        path = self.path = req.path.replace("//", "/")
        path_arr = [] if path == '/' else path.split('/')
        self.path_arr = list(filter(lambda x: len(x) > 0, path_arr))
        # 复制headers
        self.headers = dict(req.headers)
        self.cookies = dict(req.cookies)
        self.query_arguments = dict(req.query_arguments)
        self.arguments = dict(req.arguments)
        self.body = req.body
        # 解析数据
        params = {}
        for key in req.query_arguments:
            params[key] = hdl.get_query_argument(key)
        for key in req.arguments:
            params[key] = hdl.get_argument(key)

        # json
        if self.headers.get('content-type', '').find('application/json') > -1:
            try:
                body = self.body.decode('utf-8')
                content_params = json.loads(body)
                params = {**params, **content_params}
            except BaseException as e:
                logger.error("json请求数据解析异常")
                logger.error(e)

        self.params = params

    def is_post(self):
        return self.method == 'POST'

    def is_get(self):
        return self.method == 'GET'

    def is_ajax(self):
        return True if self.headers.get('x-requested-with') == 'XMLHttpRequest' else False

    def ip(self):
        return self.remote_ip


class Response:
    """返回头"""

    def __init__(self):
        self.status = 200
        self.status_msg = None
        self.headers = {}
        self.cookies = {}
        self.body = None     # 返回内容

    def set_header(self, key, val):
        self.headers[key] = val

    def write(self, body):
        if self.body is None:
            self.body = bytes()
        if isinstance(body, bytes) is False:
            body = bytes(body, encoding="utf8")
        self.body += body

    def finish(self, hdl):
        # 写入header
        if len(self.headers) > 0:
            for k, v in self.headers.items():
                hdl.set_header(k, v)

        # 写入 cookie
        if len(self.cookies) > 0:
            for k, v in self.cookies.items():
                hdl.set_cookie(k, v['val'], max_age=v['max_age'])

        # 将body写入tornado
        if self.body is not None:
            hdl.write(self.body)
