import signal, logging, mimetypes
import importlib, time, os, inspect
from typing import Optional, Awaitable
from concurrent.futures import ThreadPoolExecutor

import config
import tornado
from tornado import web
from tornado.concurrent import run_on_executor
from .exception import *
from .controller import Controller
from .settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProcessorController(web.RequestHandler):

    executor = ThreadPoolExecutor(max_workers=config.Config.web_thr_count(SETTINGS['pro_thr_num']))

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        self.request.method = 'GET'
        resp_content = yield self._dispose(*args)
        if resp_content is True:
            self.finish()
            return
        if self.response_write(resp_content) is False:
            self.finish()
            return

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        self.request.method = 'POST'
        resp_content = yield self._dispose(*args)
        if resp_content is True:
            # self.finish()
            return
        if self.response_write(resp_content) is False:
            self.finish()
            return

    def return_file(self, path):
        """
        如果是文件且存在就处理
        PS: http://127.0.0.1:8107/static/assets/img/logo.png
        """
        file_path = "{}{}".format(SETTINGS['static_path'], path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime = mimetypes.guess_type(file_path)
            self.set_header('Content-Type', mime[0])
            self.set_header('cache-control', "max-age={}".format(SETTINGS.get('resource_max_age', 86400)))
            # 开启此选项浏览器回直接下载文件
            # self.set_header('Content-Disposition', 'attachment; filename=' + os.path.basename(file_path))
            buf_size = 1024 * 1024 * 10
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(buf_size)
                    if not data:
                        break
                    self.write(data)

            return True

        return False

    @run_on_executor
    def _dispose(self, *args):
        try:
            # 初始数据
            self._on_mtime = int(time.time() * 1000)
            self._is_finish = False
            # 请求信息
            request = self.request
            request.method = 'POST' if hasattr(self, 'method') is None else request.method
            logger.debug("method={}, args={}".format(request.method, args))
            remote_ip = request.remote_ip
            path = self.path = self.request.path
            path = path.replace("//", "/")
            path_arr = self.path_arr = [] if path == '/' else path.split('/')
            # 是否是ajax请求
            self.request.is_ajax = True if request.headers.get('x-requested-with') == 'XMLHttpRequest' else False
            # 是否是资源文件下载
            if self.return_file(path):
                return True
            # 收集请求参数
            params = self.params = {}
            for key in request.arguments:
                self.params[key] = self.get_argument(key)
            logger.debug("path={}, params={}".format(path, params))

            # 寻找控制器
            controller, controller_action = self.load_controller_action(self, path, path_arr)
            controller.__initialize_request__(path, params, request)

            # 执行控制器方法
            # hooker.trigger('request_before', controller)
            ret = controller_action()
            # hooker.trigger('request_after', controller)
            return "None" if ret is None else ret

        except ResponseException as e:
            return e

        except BaseException as e:
            logging.exception(e)
            return "请求异常：{}".format(e)

        finally:
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
        ret = []
        for it in os.listdir(path):
            if it[2:] != '__':
                ret.append(it)
        ret.sort()
        return ret

    @classmethod
    def scan_file(cls, path):
        ret = []
        for it in os.listdir(path):
            if it[:1] != '_':
                ret.append(it)
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
    def load_controller_action(cls, pro_obj, path, path_arr):
        """找到对应控制器和方法"""
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

        module, controller, action = pa[0], '.'.join(pa[1:-1]), pa[-1]
        module, controller, action = module.lower(), controller.lower(), action.lower()
        if module in cls.MODULES:
            if controller in cls.MODULES[module]:
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
        """返回结果统一处理"""
        # headers
        self.set_status(status_code)
        self.set_header('Server', 'quickpython-1.05')
        self.set_header('Accept-Language', 'zh-CN,zh;q=0.9')
        self.set_header('Content-Type', 'text/html; charset={}'.format(SETTINGS['encoding']))

        if isinstance(ret, ResponseRenderException):
            return self.render(template_name=ret.tpl_name, **ret.data)
        if isinstance(ret, ResponseNotFoundException):
            status_code = 404
            ret = ret.text
        if isinstance(ret, ResponseTextException):
            ret = ret.text

        self.set_status(status_code)
        # 返回json
        request_type = self.request.headers.get("Content-Type", '').lower()
        if request_type == 'application/json' or self.request.is_ajax:
            self.set_header('Content-Type', 'application/json')
            ret = ret if isinstance(ret, Result) else Result.success(ret)
            self.write(str(ret))
            return True

        # 返回html
        if self._is_finish is False:
            self.write(str(ret))
            return True

        return False

    def on_finish(self):
        self._is_finish = True
