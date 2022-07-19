"""
    Session管理器
    python-quick.session 1.0
    PS: 适配tornado

"""
import os, time
from hashlib import sha1
from quickpython.component import env, cache

CACHE_NAME = "__SESSION_CACHE__"


class Session2:
    def __init__(self, sess_id):
        self.id = sess_id


class Session:

    name = env.get('session.name', 'qp_session')
    expire = env.get('session.expire', 86400 * 7)

    def __init__(self, handler, session_name=None):
        self.name = self.name if session_name is None else session_name
        self.sess_id = handler.get_cookie(self.name)
        self.__data = None
        if self.sess_id is None or len(self.sess_id) <= 16:
            self.sess_id = self._gen_session_id()
            self.__data = {}
            cache.set(self._cache_name, {}, self.expire)
            handler.set_cookie(self.name, self.sess_id, max_age=self.expire)
        else:
            self.__data = cache.get(self._cache_name, {}, self.expire)

    @classmethod
    def _gen_session_id(cls):
        return sha1(bytes('%s%s' % (time.time(), os.urandom(32)), encoding='utf-8')).hexdigest()

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)

    def get(self, key, def_val=None):
        return self.__data.get(key, def_val)

    def set(self, key, val):
        if val is None:
            return self.delete(key)
        self.__data[key] = val
        self._data_save()

    def delete(self, key):
        if key in self.__data:
            del self.__data[key]
            self._data_save()

    def destroy(self):
        self.__data = {}
        cache.delete(self._cache_name)

    def _data_save(self):
        cache.set(self._cache_name, self.__data, True)

    @property
    def _cache_name(self):
        return CACHE_NAME + self.sess_id
