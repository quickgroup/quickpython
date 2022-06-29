import logging
from libs.utils import Utils
from quickpython.server.exception import *
from quickpython.component.session import Session
from quickpython.component.result import Result
from quickpython.server.settings import SETTINGS
from .request import Request


class Controller:
    tpl_style = 'default'
    tpl_ext = 'html'

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.pro_obj = None         # type:web.processor.ProcessorController
        self.params = {}            # 请求数据
        self.assign_data = {        # 默认注入参数
            'version': self._version,
            'Utils': Utils,
        }

    @property
    def _version(self):
        # return Utils.stime() if SETTINGS['debug'] else SETTINGS['version']
        return SETTINGS['version']

    def initialize(self):
        pass

    def __initialize__(self, obj, module: str, controller: str, action: str):
        self.pro_obj = obj
        self.module = module
        self.controller = controller.replace('.', '/')
        self.action = action

    def __initialize_request__(self, path, params, request):
        self.path = path
        self.params = params
        self.request = Request(request)
        self.headers = request.headers
        self.cookies = request.cookies
        self.session = request.session = Session(self)
        self.initialize()

    def render(self, *args, **kwargs):
        args = list(args)
        if args[0].find(self.tpl_ext) > -1:     # type:str
            args[0] = "{}/{}".format(self.controller, args[0])
        else:
            args[0] = "{}/{}.{}".format(self.controller, args[0], self.tpl_ext)     # 追加模板后缀
        args[0] = "{}/view/{}/{}".format(self.module, self.tpl_style, args[0])
        # return self.pro_obj.render(template_name=args[0], __config="", **{**self._assign_data, **kwargs})

        raise ResponseRenderException(args[0], {**{**self.assign_data, **kwargs}})
        # return args[0], {**{**self._assign_data, **kwargs}}

    def __getattr__(self, name):
        return getattr(self.pro_obj, name)

    def view(self, *args, **kwargs):
        if len(args) == 0:
            args = "{}.{}".format(self.action, self.tpl_ext),
        return self.render(*args, **kwargs)
