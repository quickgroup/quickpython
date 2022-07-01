import os, threading, time, types, logging
import json, pickle
from ..config import Config

log = logging.getLogger(__name__)

# default、file
CACHE_TYPE = 'file'
ENCODE = "utf8"
serialize_type = 'pickle'

TIME_K = 't'
VAL_K = 'v'


class QPCache:

    TIMEOUT = 1800
    __DATA__ = {}
    __LOCK__ = threading.Lock()

    # def __init__(self, name=CACHE_TYPE):
    #     self.name = name

    @staticmethod
    def gen_key(obj):
        return str(obj)

    @staticmethod
    def stime():
        return int(time.time())

    @classmethod
    def _read_file(cls, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                try:
                    content = f.read()
                    if len(content) > 0:
                        if serialize_type == 'pickle':
                            return pickle.loads(content)

                        content = bytes(content).decode(ENCODE)
                        return json.loads(content, encoding=ENCODE)
                except BaseException as e:
                    # pass
                    log.exception(e)
        return {}

    @classmethod
    def _write_file(cls, path, data):
        data = {} if data is None else data
        with open(path, 'wb') as f:
            if serialize_type == 'pickle':
                content = pickle.dumps(data)        # 不支持序列化的对象会报错 none not call
            else:
                data = data if isinstance(data, dict) else {}
                content = json.dumps(data, ensure_ascii=False)
                content = content.encode(ENCODE)
            f.write(content)

    @classmethod
    def _load_data(cls):
        if CACHE_TYPE.upper() == 'FILE':
            file_path = "{}/CACHE.file".format(Config.CACHE_PATH)
            return cls._read_file(file_path)
        else:
            return cls.__DATA__

    @classmethod
    def _write_data(cls, data):
        if CACHE_TYPE.upper() == 'FILE':
            file_path = "{}/CACHE.file".format(Config.CACHE_PATH)
            cls._write_file(file_path, data)
        else:
            cls.__DATA__ = data

    @classmethod
    def get(cls, key, def_val=None, timeout=TIMEOUT):
        cls.__check_overtime__()
        data = cls._load_data()
        with cls.__LOCK__:
            if key in data:
                item = data[key]
                if item[TIME_K] > cls.stime():
                    return item[VAL_K]

            # 默认数据
            if def_val is not None:
                def_val = def_val() if isinstance(def_val, types.FunctionType) else def_val
                data[key] = {TIME_K: cls.stime() + timeout, VAL_K: def_val}
                cls._write_data(data)

            return def_val

    @classmethod
    def set(cls, key, val, timeout=TIMEOUT):
        """timeout: 60s"""
        cls.__check_overtime__()
        if val is None:
            return cls.delete(key)

        data = cls._load_data()
        with cls.__LOCK__:
            if timeout is True and key in data:     # 继承原来的超时时间
                data[key] = {TIME_K: data[key][TIME_K], VAL_K: val}
            else:
                data[key] = {TIME_K: cls.stime() + timeout, VAL_K: val}
            cls._write_data(data)

    @classmethod
    def delete(cls, key):
        data = cls._load_data()
        with cls.__LOCK__:
            if key in data:
                data.pop(key)
                cls._write_data(data)

    @classmethod
    def destroy(cls, key):
        cls._write_data({})

    @classmethod
    def __check_overtime__(cls):
        data = cls._load_data()
        with cls.__LOCK__:
            keys = list(data.keys())
            is_over_item = False
            for key in keys:
                item = data[key]
                if item[TIME_K] < cls.stime():
                    data.pop(key)
                    is_over_item = True
            if is_over_item:
                cls._write_data(data)


    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)


cache = QPCache()
