import signal, logging, mimetypes
import importlib, time, os, inspect
from typing import Optional, Awaitable, Any
from concurrent.futures import ThreadPoolExecutor

from .common import *

import quickpython
from quickpython.server import Config
from quickpython.component.function import *
from quickpython.component.result import Result
from .exception import *
from .contain import Controller, Request, Response, HandlerHelper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
encoding = Config.SETTINGS['encoding']
DS = r"/"


class Application:
    pass


class QuickPythonHandler:

    def __init__(self, application: Application, request: Request, hdl=None):
        self.application = application
        self.request = request
        self.response = Response()
        self._hdl = hdl         # tornado的hdl
        self.params = {}        # 收集到的请求参数
        self._is_finish = False

    @classmethod
    def action(cls, path, headers=None, params=None, body=None):
        """本地接口直接调用"""
        request = Request()
        request.path = path
        request.headers = headers
        request.params = params
        request.body = body
        handler = QuickPythonHandler(Application(), request)
        handler.__dispose__()
        return handler.response.body

    def __dispose__(self):
        try:
            ret = self.__dispose()
        except BaseException as e:
            ret = e

        if ret is not True:
            self.response_write(ret)

        self.finish()

    def __dispose(self):
        ret = None
        try:
            # 初始
            request = self.request
            self._on_mtime = int(time.time() * 1000)
            self._is_finish = False         # 请求是否结束
            self._is_res_request = False    # 是否是资源请求
            # 请求处理
            request.parse_path()
            logger.debug("method={}, path={}".format(request.method, request.path))

            # 是否是资源文件下载（需要对upload进行鉴权处理
            if HandlerHelper.return_file(self, request.path):
                self._is_res_request = True
                return True

            # 收集请求参数
            params = self.params = self.request.params
            logger.debug("path={}, params={}".format(request.path, params))

            # 寻找控制器
            controller, controller_action = self.find_controller_action(self, self.request)
            controller.__initialize_request__(request.path, params, self.request)

            # 执行控制器方法
            # hooker.trigger('request_before', controller)
            ret = controller_action()
            # hooker.trigger('request_after', controller)

            ret = "None" if ret is None else ret
            return ret

        except ResponseException as e:
            return e
        except tornado.template.ParseError as e:
            logger.exception(e)
            return ResponseException("页面模板异常：{}".format(str(e)), code=500)
        except BaseException as e:
            logging.exception(e)
            return "系统异常：{}".format(e)
        finally:
            if self._is_res_request is False:       # 只记录控制器日志
                logging.info("{} {} {}ms".format(self.get_status(), self.request.path, int(time.time() * 1000) - self._on_mtime))

    MODULES = {}

    @classmethod
    def load_module(cls):
        """预加载控制器"""
        if len(cls.MODULES) > 0:
            return

        app = "app"
        c_dir_name = "controller"

        def load_method(c_class):
            methods = {}
            for it in dir(c_class):
                if it[:1] == '_': continue
                if it == 'initialize': continue
                it_cls = getattr(c_class, it)
                if inspect.isfunction(it_cls):
                    methods[it] = it

            return methods

        def load_controller(c_path, p_name=""):
            controllers = {}
            for c in cls.scan_file(c_path):
                cls_file_path = c_path + "/" + c
                if os.path.isfile(cls_file_path):
                    if c[-3:] != ".py": continue
                    cls_file_path = cls_file_path.replace('/', '.')
                    c_file = importlib.import_module(cls_file_path.replace('.py', ''))
                    # logger.debug("cls_file_path={}\nc_file={}\ndir={}".format(cls_file_path, c_file, dir(c_file)))
                    # 扫描文件里的控制器类
                    for cls_name in cls.scan_file_class(c_file):
                        c_class = getattr(c_file, cls_name)
                        if isinstance(c_class, type) is False:
                            continue
                        if c_class == Controller:
                            continue
                        if issubclass(c_class, Controller):
                            c_name = cls_name.lower().replace("controller", '')
                            if len(p_name) > 0:
                                c_name = p_name + "." + c_name
                            controllers[c_name] = {'obj': c_class(), 'm': load_method(c_class)}

                elif os.path.isdir(cls_file_path):
                    curr_name = cls_file_path.split('/')[-1]
                    if len(p_name) > 0:
                        curr_name = p_name + "." + curr_name
                    controller_subs = load_controller(cls_file_path, curr_name)
                    # logger.debug("controller_subs={}".format(controller_subs))
                    controllers = {**controllers, **controller_subs}

            return controllers

        for m in cls.scan_dir(app):
            c_path = "{}/{}/{}".format(app, m, c_dir_name)
            cls.MODULES[m] = load_controller(c_path)        # 加载模块控制器

        logger.debug("cls.MODULES={}".format(cls.MODULES))

    @classmethod
    def scan_dir(cls, path):
        ret = list(filter(lambda x: os.path.isdir(path + DS + x) and x.find('__') == -1, os.listdir(path)))
        ret.sort()
        return ret

    @classmethod
    def scan_file(cls, path):
        ret = list(filter(lambda x: os.path.isfile(path + DS + x) and x.find('__') == -1, os.listdir(path)))
        ret.sort()
        return ret

    @classmethod
    def scan_file_class(cls, file):
        ret = []
        for it in dir(file):
            if it[-2:] != '__':
                ret.append(it)
        return ret

    @classmethod
    def find_controller_action(cls, pro_obj, request):
        """找到对应控制器和方法"""
        path, path_arr = request.path, request.path_arr
        pa = path_arr[1:] if len(path_arr) > 0 and path_arr[0] == '' else path_arr
        if len(pa) == 0 or pa[0] == '':
            pa.extend(["index", "index", "index"])
        elif len(pa) == 1:
            pa.extend(["index", "index"])
        elif len(pa) == 2:
            pa.extend(["index"])
        else:
            pass
        logger.debug("path_arr={} -> pa={}".format(path_arr, pa))

        cls.load_module()
        url_html = Config.SETTINGS['url_html']

        module, controller, action = pa[0], '.'.join(pa[1:-1]), pa[-1]
        module, controller, action = module.lower(), controller.lower(), action
        if module in cls.MODULES:
            if controller in cls.MODULES[module]:
                action = action.replace(url_html, '')
                if action in cls.MODULES[module][controller]['m']:
                    obj = cls.MODULES[module][controller]['obj']
                    obj = obj.__class__()
                    obj.__initialize__(pro_obj, module, controller, action)
                    return obj, getattr(obj, action)
                else:
                    raise ResponseNotFoundException("方法不存在：{}".format(action))
            else:
                raise ResponseNotFoundException("控制器不存在：{}".format(controller))
        else:
            raise ResponseNotFoundException("模块不存在：{}".format(module))

    def response_write(self, ret, status_code=200):
        return self._response_write(ret, status_code)

    def _response_write(self, ret, status_code=200):
        """返回结果统一处理"""
        # headers
        self.set_status(status_code)
        self.set_header('Server', quickpython.name + '-' + quickpython.version)
        self.set_header('Accept-Language', 'zh-CN,zh;q=0.9')
        # 分别处理
        if isinstance(ret, ResponseRenderException):
            try:
                return self.render(template_name=ret.tpl_name, **ret.data)
            except BaseException as e:
                logger.exception(e)
                ret = ResponseException("页面异常：{}".format(str(e)), code=500)
                return HandlerHelper.render_response(self, ret)

        elif isinstance(ret, ResponseFileException):
            return HandlerHelper.return_file(self, ret.file, ret.mime)
        elif isinstance(ret, ResponseException):
            return HandlerHelper.render_response(self, ret)
        elif isinstance(ret, AppException):
            status_code = 500
            ret = str(ret)

        self.set_status(status_code)
        # 返回json
        request_type = self.request.headers.get("Content-Type", '').lower()
        if request_type == 'application/json' or self.request.is_ajax():
            self.set_header('Content-Type', 'application/json; charset={}'.format(encoding))
            ret = ret if isinstance(ret, Result) else Result.result(status_code, ret, None)
            self.write(str(ret))
            return True

        # 返回html
        if self._is_finish is False:
            self.set_header('Content-Type', 'text/html; charset={}'.format(encoding))
            self.write(str(ret))
            return True

        return False

    def get_status(self):
        return self.request.status

    def set_status(self, status):
        self.response.status = status

    def get_cookie(self, k):
        return self.request.cookies.get(k)

    def set_cookie(self, key, val, max_age=None):
        self.response.cookies[key] = {'val': val, 'max_age': max_age}

    def set_header(self, key, val):
        self.response.set_header(key, val)

    def write(self, content=None):
        self.response.write(content)

    def render(self, template_name, **kwargs):
        """渲染模板"""
        if self._hdl is not None:
            html = self._hdl.render_string(template_name, **kwargs)
            self.response.write(html)

    def finish(self):
        """结束"""
        if self._hdl is not None:
            self.response.finish(self._hdl)

    def on_finish(self):
        self._is_finish = True


class TornadoProcessorHandler(web.RequestHandler):
    """嫁接tornado框架"""

    executor = ThreadPoolExecutor(max_workers=Config.web_thr_count(Config.SETTINGS['pro_thr_num']))

    def initialize(self):
        request = Request()
        request.__load_from_tornado__(self.request, self)
        self._hdl = QuickPythonHandler(Application(), request, self)

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        self._hdl.request.method = 'GET'
        yield self._dispose(*args)

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        self._hdl.request.method = 'POST'
        yield self._dispose(*args)

    @run_on_executor
    def _dispose(self, *args):
        return self._hdl.__dispose__()

    def on_finish(self):
        self._hdl.on_finish()
