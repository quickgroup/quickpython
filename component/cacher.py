"""
    缓存器基类
"""
import base64
import os, threading, time, types, logging
import json, pickle, base64

logger = logging.getLogger(__name__)

TIME_K = 't'
VAL_K = 'v'


class CacherBase:

    TIMEOUT = 1800
    TIMEOUT_HOUR = 3600
    __DATA__ = {}
    # __LOCK__ = threading.Lock()

    @staticmethod
    def _gen_key(obj):
        return str(obj)

    @staticmethod
    def _stime():
        return int(time.time())

    def ttl(self, key):
        return 0

    def get(self, key, def_val=None, timeout=TIMEOUT):
        pass

    def set(self, key, val, timeout=TIMEOUT):
        pass

    def delete(self, key):
        pass

    def destroy(self):
        pass

    def __check_overtime__(self):
        pass

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)


from quickpython.config import Config, env
from quickpython.component.flock import FLock

ENCODE = "utf8"


class QPFileCache(CacherBase):

    CACHE_FILE = Config.CACHE_PATH + "/cache.file"
    LOCK_FILE = CACHE_FILE + ".lock"

    @classmethod
    def _read_file(cls, path):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                try:
                    content = f.read()
                    if len(content) > 0:
                        return pickle.loads(content)
                except BaseException as e:
                    logger.exception(e)
        return {}

    @classmethod
    def _write_file(cls, path, data):
        data = {} if data is None else data
        with open(path, 'wb') as f:
            content = pickle.dumps(data)
            f.write(content)

    @classmethod
    def _load_data(cls):
        cls.__DATA__ = cls._read_file(cls.CACHE_FILE)
        return cls.__DATA__

    @classmethod
    def _write_data(cls, data):
        cls.__DATA__ = data         # 本质还是要在内存中存在，存在多机部署共享问题
        cls._write_file(cls.CACHE_FILE, data)

    def ttl(self, key, data=None):
        if data is None:
            data = self._load_data()
        if key in data:
            return data[key][TIME_K] - self._stime()
        return super().ttl(key)

    def get(self, key, def_val=None, timeout=CacherBase.TIMEOUT):
        with FLock(self.LOCK_FILE):
            self.__check_overtime__()
            data = self._load_data()
            if key in data:
                item = data[key]
                if item[TIME_K] > self._stime():
                    return item[VAL_K]
            else:
                logger.debug("key={} not fund".format(key))

            # 默认数据
            if def_val is not None:
                def_val = def_val() if isinstance(def_val, types.FunctionType) else def_val
                data[key] = {TIME_K: self._stime() + timeout, VAL_K: def_val}
                self._write_data(data)

            return def_val

    def set(self, key, val, timeout=CacherBase.TIMEOUT):
        """timeout: 60s"""
        with FLock(self.LOCK_FILE):
            self.__check_overtime__()
            if val is None:
                return self.delete(key)

            data = self._load_data()
            if timeout is True and key in data:     # 继承原来的超时时间
                data[key] = {TIME_K: data[key][TIME_K], VAL_K: val}
            else:
                data[key] = {TIME_K: self._stime() + timeout, VAL_K: val}

            self._write_data(data)

    def delete(self, key):
        with FLock(self.LOCK_FILE):
            data = self._load_data()
            if key in data:
                data.pop(key)
                self._write_data(data)

    def destroy(self):
        self._write_data({})

    def __check_overtime__(self):
        data = self._load_data()
        keys = list(data.keys())
        is_over_item = False
        for key in keys:
            item = data[key]
            if item[TIME_K] < self._stime():
                data.pop(key)
                is_over_item = True
        if is_over_item:
            self._write_data(data)


class QPRedisCache(CacherBase):

    HOST = env.get('redis.host', "127.0.0.1")
    PORT = env.get('redis.port', 6379)
    PASSWORD = env.get('redis.password', '')
    DATABASE = env.get('redis.database', 8)
    PREFIX = ""

    def __init__(self):
        from redis import Redis, ConnectionPool
        pool = ConnectionPool(host=self.HOST, port=self.PORT, password=self.PASSWORD, db=self.DATABASE, decode_responses=True)
        conn = Redis(connection_pool=pool)
        self.__conn = conn

    def ttl(self, key):
        return self.__conn.ttl(key)

    def get(self, key, def_val=None, timeout=CacherBase.TIMEOUT):
        """
        :param def_val: object 默认返回数据，可以是int、function
        :param timeout: int 超时时间，当def_val不为空时，必须设置该值
        """
        key = self.PREFIX + key
        try:
            content = self.__conn.get(key)
            if content is None:
                if def_val is not None:
                    def_val = def_val() if isinstance(def_val, types.FunctionType) else def_val
                    self.set(key, def_val, timeout)
                    return def_val
                else:
                    return def_val

            content = base64.b64decode(str(content))
            val = pickle.loads(content)
            # logger.info("缓存时间剩余 {}, key={}".format(self.ttl(key), key))

        except BaseException as e:
            logger.exception(e)
            self.__conn.delete(key)
            val = {}

        return val

    def set(self, key, val, timeout=CacherBase.TIMEOUT):
        content = pickle.dumps(val)
        content = str(base64.b64encode(content), encoding='utf8')

        # 更新某值
        if timeout is True and self.__conn.get(key) is not None:
            ttl = self.ttl(key)
            ttl = CacherBase.TIMEOUT if ttl is None or ttl == -1 else ttl
            self.__conn.set(key, content, ttl)
        else:
            self.__conn.set(key, content, ex=timeout)

    def delete(self, key):
        self.__conn.delete(key)


class QPMemoryCache(CacherBase):

    LOCK_FILE = Config.CACHE_PATH + "/cache.file" + ".lock"

    __DATA__ = {}

    @classmethod
    def _load_data(cls):
        return cls.__DATA__

    @classmethod
    def _write_data(cls, data):
        cls.__DATA__ = data

    def ttl(self, key, data=None):
        if data is None:
            data = self._load_data()
        if key in data:
            return data[key][TIME_K] - self._stime()
        return super().ttl(key)

    def get(self, key, def_val=None, timeout=CacherBase.TIMEOUT):
        with FLock(self.LOCK_FILE):
            self.__check_overtime__()
            data = self._load_data()
            if key in data:
                item = data[key]
                if item[TIME_K] > self._stime():
                    return item[VAL_K]
            else:
                logger.debug("key={} not fund".format(key))

            # 默认数据
            if def_val is not None:
                def_val = def_val() if isinstance(def_val, types.FunctionType) else def_val
                data[key] = {TIME_K: self._stime() + timeout, VAL_K: def_val}
                self._write_data(data)

            return def_val

    def set(self, key, val, timeout=CacherBase.TIMEOUT):
        """timeout: 60s"""
        with FLock(self.LOCK_FILE):
            self.__check_overtime__()
            if val is None:
                return self.delete(key)

            data = self._load_data()
            if timeout is True and key in data:     # 继承原来的超时时间
                data[key] = {TIME_K: data[key][TIME_K], VAL_K: val}
            else:
                data[key] = {TIME_K: self._stime() + timeout, VAL_K: val}

            self._write_data(data)

    def delete(self, key):
        with FLock(self.LOCK_FILE):
            data = self._load_data()
            if key in data:
                data.pop(key)
                self._write_data(data)

    def destroy(self):
        self._write_data({})

    def __check_overtime__(self):
        data = self._load_data()
        keys = list(data.keys())
        is_over_item = False
        for key in keys:
            item = data[key]
            if item[TIME_K] < self._stime():
                data.pop(key)
                is_over_item = True
        if is_over_item:
            self._write_data(data)


class QPCache(CacherBase):

    __ENGINE_MAP__ = {}

    def __init__(self, name='default', type_=None):
        if type_ is None:
            from quickpython.server.settings import CACHE
            type_ = CACHE.get('type', 'memory')
        if name not in self.__ENGINE_MAP__:
            self.__ENGINE_MAP__[name] = self.__load_engine(type_)
        self._target = self.__ENGINE_MAP__[name]

    @staticmethod
    def __load_engine(type_: str):
        if type_.upper() == 'FILE': engine = QPFileCache()
        elif type_.upper() == 'REDIS': engine = QPRedisCache()
        elif type_.upper() == 'MEMORY': engine = QPMemoryCache()
        else: raise Exception('不支持的缓存引擎：{}'.format(type_))
        return engine

    def __getattribute__(self, item):
        if item in dir(CacherBase):
            return getattr(self._target, item)
        return object.__getattribute__(self, item)


cache = QPCache()


if __name__ == '__main__':
    import threading
    formatter_str = '%(asctime)s %(levelname)s [%(filename)s:%(funcName)s:%(lineno)d]\t%(message)s'
    logging.basicConfig(format=formatter_str, level=logging.DEBUG, handlers=[logging.StreamHandler()])
    cache_key = 'test_cache'
    cache.delete(cache_key)


    def opt(num):
        ident = threading.current_thread().ident
        my_cache_key = cache_key + "_" + str(num)

        content = cache.get(my_cache_key, '')
        logger.info('content={}'.format(content))
        content += "{}, thr={}\n".format(num, ident)
        logger.info('content-2={}'.format(content))
        cache.set(my_cache_key, content)

    thr_list = [threading.Thread(target=opt, args=(it,)) for it in range(100)]
    [thr.start() for thr in thr_list]
    [thr.join() for thr in thr_list]

    for idt in range(len(thr_list)):
        logger.info('最后结果={}'.format(cache.get(cache_key + "_" + str(idt))))
