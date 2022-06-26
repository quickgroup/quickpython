"""
    Session管理器
    python-quick.session 1.0
    PS: 适配tornado

"""
import os, time
from hashlib import sha1
from quickpython.component.env import env


class Session2:

    def __init__(self, sess_id):
        self.id = sess_id


class Session:

    name = env.get('session.name', 'qp_session')
    expire = env.get('session.expire', 60)

    _CACHE = {
        # session_id: {}
    }

    def __init__(self, handler, session_name=None):
        self.handler = handler
        self.name = self.name if session_name is None else session_name
        self.sess_id = self.handler.get_cookie(self.name)
        if self.sess_id is None:
            self.sess_id = self._gen_session_id()
            self._CACHE[self.sess_id] = {}
            self.handler.set_cookie(self.name, self.sess_id, max_age=self.expire)

    @classmethod
    def _gen_session_id(cls):
        return sha1(bytes('%s%s' % (time.time(), os.urandom(32)), encoding='utf-8')).hexdigest()

    def __getitem__(self, item):
        return self._CACHE[self.sess_id].get(item)

    def __setitem__(self, key, value):
        self._CACHE[self.sess_id][key] = value

    def __delitem__(self, key):
        if key in self._CACHE[self.sess_id]:
            del self._CACHE[self.sess_id][key]

    def get(self, key, def_val=None):
        if self.sess_id in self._CACHE:
            return self._CACHE[self.sess_id].get(key, def_val)
        return def_val

    def set(self, key, val):
        if self.sess_id not in self._CACHE:
            self._CACHE[self.sess_id] = {}
        self._CACHE[self.sess_id][key] = val

    def delete(self):
        """从大字典删除session_id"""
        del self._CACHE[self.sess_id]

