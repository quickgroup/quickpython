import quickpython.component.function as functions
from quickpython.config import Config, env


# app配置
SETTINGS = {
    'debug': env.get('app.debug', False),
    'port': env.get('app.port', 32000),
    'version': '0.2.1',
    'template_path': 'app',
    'public_path': 'public',
    'static_path': 'public/static',
    'ui_methods': functions,
    'pro_thr_num': None,        # 默认是CPU核心数的线程数量
    # 环境配置
    'lang': 'zh-cn',
    'timezone': 'PRC',
    'encoding': 'utf-8',        # 全局框架文件默认编码
    # 应用设置
    'default_module': 'index',
    'default_controller': 'index',
    'default_action': 'index',
    'url_convert': True,    # 自动转换为控制器方法
    'url_route_on': False,
    'url_html': '.html',
    # 模板配置
    'template': {
        'view_path': '',
        'view_suffix': 'html',
        'cache': True,
    },
    'view_replace_str': {
        '__PUBLIC__': '',
        '__ROOT__': '',
        '__CDN__': '',
    },
    'dispatch_success_tmpl': "",
    'dispatch_error_tmpl': "",
    'dispatch_exception_tmpl': "",
    'error_message': "你所浏览的页面暂时无法访问",
    'exception_handle': '',
    # 验证码
    'captcha': {
        'code_set': '2345678abcdefhijkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXY',
        'font_size': 18,
        'height': 40,
        'width': 130,
        'count': 5,
    },
    #
    'resource_max_age': 86400,
}

# session配置
SESSIONS = {
    'prefix': 'qp_',
    'type': "",
    'expire': 86400 * 7,
}

# 日志配置
LOGGING = {
    'default': {
        'level': 'DEBUG',
    }
}

# 路由
from .processor import ProcessorHandler
ROUTES = [
    (r"/(.*)", ProcessorHandler),    # 默认处理控制器
]

# TODO::将配置加载到env
for it, val in SESSIONS.items():
    env.set(it, val)
