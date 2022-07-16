"""
    缓存器基类
"""
import os, threading, time, types, logging


class CacherBase:

    TIMEOUT = 1800
    __DATA__ = {}
    __LOCK__ = threading.Lock()

    @staticmethod
    def _gen_key(obj):
        return str(obj)

    @staticmethod
    def _stime():
        return int(time.time())

    @classmethod
    def _read_file(cls, path):
        return {}

    @classmethod
    def _write_file(cls, path, data):
        return {}

    @classmethod
    def _load_data(cls):
        return cls.__DATA__

    @classmethod
    def _write_data(cls, data):
        pass

    @classmethod
    def get(cls, key, def_val=None, timeout=TIMEOUT):
        pass

    @classmethod
    def set(cls, key, val, timeout=TIMEOUT):
        pass

    @classmethod
    def delete(cls, key):
        pass

    @classmethod
    def destroy(cls, key):
        pass

    @classmethod
    def __check_overtime__(cls):
        pass

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)