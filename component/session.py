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
        handler = handler
        self.name = self.name if session_name is None else session_name
        self.sess_id = handler.get_cookie(self.name)
        if self.sess_id is None:
            self.sess_id = self._gen_session_id()
            cache.set(self._cache_name, {}, self.expire)
            handler.set_cookie(self.name, self.sess_id, max_age=self.expire)

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
        return self._data().get(key, def_val)

    def set(self, key, val):
        if val is None:
            return self.delete(key)
        data = self._data()
        data[key] = val
        self._data_save(data)

    def delete(self, key):
        data = self._data()
        if key in data:
            del data[key]
            self._data_save(data)

    def destroy(self):
        """从大字典删除session_id"""
        # data = cache.get(CACHE_NAME, {})
        # del data[self.sess_id]
        # self._data_save(data)
        cache.delete(CACHE_NAME)

    def _data(self):
        return cache.get(self._cache_name, {})

    @property
    def _cache_name(self):
        return CACHE_NAME + self.sess_id

    def _data_save(self, data):
        cache.set(self._cache_name, data, True)
