import logging
from quickpython.component.session import Session
from quickpython.server.exception import *


class Controller:
    tpl_style = 'default'
    tpl_ext = 'html'

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.pro_obj = None         # type:web.processor.ProcessorController
        self.params = {}            # 请求数据
        self.assign_data = {}       # 默认注入参数

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
        self.headers = request.headers
        self.cookies = request.cookies
        self.session = Session(self)
        self.initialize()

    def render(self, *args, **kwargs):
        args = list(args)
        if args[0].find(self.tpl_ext) > -1:     # type:str
            args[0] = "{}/{}".format(self.controller, args[0])
        else:
            args[0] = "{}/{}.{}".format(self.controller, args[0], self.tpl_ext)
        args[0] = "{}/view/{}/{}".format(self.module, self.tpl_style, args[0])
        # return self.pro_obj.render(template_name=args[0], __config="", **{**self._assign_data, **kwargs})

        raise ResponseRenderException(args[0], {**{**self.assign_data, **kwargs}})
        # return args[0], {**{**self._assign_data, **kwargs}}

    def __getattr__(self, name):
        return getattr(self.pro_obj, name)

    def view(self, **kwargs):
        view_path = "{}.{}".format(self.action, self.tpl_ext)
        return self.render(view_path, **kwargs)
