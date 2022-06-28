import threading, time, types


class QPCache:

    TIMEOUT = 1800
    __DATA__ = {}
    __LOCK__ = threading.Lock()

    # def __init__(self, name='default'):
    #     self.name = name

    @staticmethod
    def gen_key(obj):
        return str(obj)

    @staticmethod
    def stime():
        return int(time.time())

    @classmethod
    def get(cls, key, def_val=None, timeout=TIMEOUT):
        cls.__check_overtime__()
        with cls.__LOCK__:
            if key in cls.__DATA__:
                item = cls.__DATA__[key]
                if item['time'] > cls.stime():
                    return item['val']

            # 默认数据
            if def_val is not None:
                def_val = def_val() if isinstance(def_val, types.FunctionType) else def_val
                cls.__DATA__[key] = {'time': cls.stime() + timeout, 'val': def_val}
            return def_val

    @classmethod
    def set(cls, key, val, timeout=TIMEOUT):
        """timeout: 60s"""
        cls.__check_overtime__()
        with cls.__LOCK__:
            cls.__DATA__[key] = {'time': cls.stime() + timeout, 'val': val}

    @classmethod
    def remove(cls, key):
        """timeout: 60s"""
        with cls.__LOCK__:
            if key in cls.__DATA__:
                cls.__DATA__.pop(key)

    @classmethod
    def __check_overtime__(cls):
        with cls.__LOCK__:
            keys = list(cls.__DATA__.keys())
            for key in keys:
                item = cls.__DATA__[key]
                if item['time'] < cls.stime():
                    cls.__DATA__.pop(key)


cache = QPCache()
