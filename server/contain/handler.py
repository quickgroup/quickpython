import json, logging, os
import mimetypes, importlib

from tornado import web

try:
    from config import Config, env       # 应用自己的config
except:
    from quickpython.config import Config, env

from .request import Request
from ..exception import *

logger = logging.getLogger(__name__)

dispatch_jump_html = env.get("ROOT_PATH") + "/quickpython/view/jump.html"
exception_html = env.get("ROOT_PATH") + "/quickpython/view/exception.html"


class HandlerHelper:

    @staticmethod
    def before(hdl: web.RequestHandler):
        request = hdl.request = Request(hdl.request)
        request.method = 'POST' if hasattr(hdl, 'method') is None else request.method
        # 用户IP
        hdl.client_ip = request.remote_ip
        # 路径处理
        path = hdl.path = hdl.request.path.replace("//", "/")
        path_arr = [] if path == '/' else path.split('/')
        hdl.path_arr = list(filter(lambda x: len(x) > 0, path_arr))
        # 是否ajax
        hdl.request.is_ajax = True if request.headers.get('x-requested-with') == 'XMLHttpRequest' else False

    @staticmethod
    def parse_params(hdl: web.RequestHandler):
        """
        解析请求数据
        支持：get、post、json
        """
        request = hdl.request
        params = {}
        for key in request.query_arguments:
            params[key] = hdl.get_query_argument(key)
        for key in request.arguments:
            params[key] = hdl.get_argument(key)

        # json
        if request.headers.get('content-type', '').find('application/json') > -1:
            try:
                body = request.body.decode('utf-8')
                content_params = json.loads(body)
                params = {**params, **content_params}
            except BaseException as e:
                logger.error("json请求数据解析异常")
                logger.error(e)

        hdl.params = request.params = params
        return params

    @staticmethod
    def render_exception(e):
        return

    @staticmethod
    def render_exception_result(e):
        return

    @classmethod
    def return_response(cls, hdl: web.RequestHandler, e: ResponseException):
        cls.return_response_code(hdl, e)
        if 200 <= e.code < 300 or (e.code == 1 or e.code == 2):
            hdl.render(dispatch_jump_html, **e.__dict__())
        else:       # 异常
            hdl.render(dispatch_jump_html, **e.__dict__())
        return True

    @classmethod
    def return_response_code(cls, hdl: web.RequestHandler, e: ResponseException):
        hdl.set_status(e.code)

    @classmethod
    def return_file(cls, hdl: web.RequestHandler, path, mime=None):
        """
        如果是文件且存在就处理
        PS: http://127.0.0.1:8107/static/assets/img/logo.png
        """
        public_path = Config.SETTINGS.get('public_path', "")
        res_max_age = Config.SETTINGS.get('resource_max_age', 86400)

        # 文件输出
        if cls._write_file(hdl, path, 0, mime):
            return True
        # 静态资源
        if cls._write_file(hdl, public_path + path, res_max_age, mime):
            return True
        return False

    @classmethod
    def _write_file(cls, hdl: web.RequestHandler, file_path, max_age=86400, mime=None):
        # 直接输出二进制内容
        if isinstance(file_path, bytes):
            hdl.set_header('content-type', "application/octet-stream" if mime is None else mime)
            hdl.write(file_path)
            return True

        # 字符串作为文件路径
        if isinstance(file_path, str) and os.path.exists(file_path) and os.path.isfile(file_path):
            if mime is not None:
                mime = mime
            else:
                mime = mimetypes.guess_type(file_path)[0]
            hdl.set_header('content-type', "application/octet-stream" if mime is None else mime)
            hdl.set_header('cache-control', "max-age={}".format(max_age))
            # 开启此选项浏览器回直接下载文件
            # self.set_header('Content-Disposition', 'attachment; filename=' + os.path.basename(file_path))
            buf_size = 1024 * 1024 * 10
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    hdl.write(data)

            return True

        return False

    __APP_PY__ = {}

    @staticmethod
    def import_app_py(py_name):
        """导入应用下的数据"""
        if py_name in HandlerHelper.__APP_PY__:
            return HandlerHelper.__APP_PY__[py_name]
        app_path = Config.APP_PATH.replace(Config.ROOT_PATH + "/", '')
        cmd_path = str(app_path + "/" + py_name).replace("\\", ".").replace(r"/", ".")
        py_obj = importlib.import_module(cmd_path)
        HandlerHelper.__APP_PY__[py_name] = py_obj
        return py_obj

