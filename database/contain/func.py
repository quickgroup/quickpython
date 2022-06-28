"""
    助手方法
"""
import importlib
import types
from inspect import isfunction


def empty(obj):
    if obj is None:
        return True
    elif hasattr(obj, '__len__') and len(obj) == 0:
        return True
    elif isinstance(obj, int) and obj == 0:
        return True
    elif isinstance(obj, str) and len(obj) == 0:
        return True
    elif isinstance(obj, list) and len(obj) == 0:
        return True
    elif isinstance(obj, dict) and len(obj) == 0:
        return True
    return False


def not_empty(obj):
    return empty(obj) is False


def load_cls(cls_path, **kwargs):
    model_path, cls_name = cls_path.rsplit(".", 1)
    module = importlib.import_module(model_path)
    cls = getattr(module, cls_name)
    return cls


def local_get(local, name, def_val=None):
    if hasattr(local, name) and not_empty(local.__getattribute__(name)):
        return local.__getattribute__(name)
    return def_val


def local_set(local, name, data):
    local.__setattr__(name, data)


def get_thr_id():
    import threading
    return threading.current_thread().ident
