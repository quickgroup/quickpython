import logging, types, time, threading, importlib
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor


class HookerBase:

    # 事件
    APP_START = 'APP_START' # 应用启动
    EXIT = 'EXIT'           # 程序退出
    SEND_EMS = 'SEND_EMS'       # 发送邮件
    SEND_SMS = 'SEND_SMS'       # 发送短信

    QUEUE_TIMEOUT = 0.001

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.__handlers = {}        # {key:[]}
        self._active = False
        self.count = 0
        self.count_lock = threading.Lock()

    def count_add(self, num=1):
        with self.count_lock:
            self.count += num

    def __run(self):
        pass

    def start(self):
        return self

    def join(self):
        pass

    def stop(self):
        pass

    def __get_handler_list(self, type_):
        if type_ not in self.__handlers:
            self.__handlers[type_] = []     # 不存在就创建
        return self.__handlers[type_]

    def listener(self, type_, handlers):
        """添加监听"""
        self.logger.debug('{} AddEventListener'.format(self.count))
        handler_list = self.__get_handler_list(type_)
        handlers = handlers if isinstance(handlers, list) else [handlers]
        for it in handlers:
            if it not in handler_list:  # 若要注册的处理器不在该事件的处理器列表中，则注册该事件
                handler_list.append(it)
        self.logger.debug(self.__handlers)
        self.count_add()

    def remove(self, type_, handler):
        """移除监听"""
        self.logger.debug('{} RemoveEventListener'.format(self.count))
        handler_list = self.__get_handler_list(type_)
        # 如果该函数存在于列表中，则移除
        if handler in handler_list:
            handler_list.remove(handler)
        if not handler_list:  # 如果函数列表为空，则从引擎中移除该事件类型
            del self.__handlers[type_]
        self.count_add()

    def __event_process__(self, type_, data):
        """处理事件"""
        self.logger.debug('{} EventProcess'.format(self.count))
        if type_ in self.__handlers:
            for handler in self.__handlers[type_]:  # 若存在，则按顺序将事件传递给处理函数执行
                self.__handler_call__(handler, type_, data)

        self.count_add()

    def __handler_call__(self, handler, type_, data):
        """触发执行该监听"""
        if isinstance(handler, str):
            method = self.__load_static_method(handler)
        elif isinstance(handler, types.FunctionType):
            method = handler
        else:
            raise Exception("未知类型回调对象：{} {} {} {}".format(type_, type(handler), handler, data))

        try:
            if data is None:
                method()
            else:
                method(data)
        except TypeError:
            self.logger.exception("方法调用异常 {}".format(method))

    _METHOD_MAP = {}

    @staticmethod
    def __load_static_method(name):
        """加载类"""
        if name not in HookerBase._METHOD_MAP:
            HookerBase._METHOD_MAP[name] = HookerBase.__find_static_method(name)
        return HookerBase._METHOD_MAP[name]

    STATIC_METHODS = {}

    @staticmethod
    def __find_static_method(path):
        """加载静态方法"""
        if path in HookerBase.STATIC_METHODS:       # 缓存的静态方法
            return HookerBase.STATIC_METHODS[path]
        # 创建
        clazz_info = str(path).split("#")
        model_path, clazz_name = clazz_info[0].rsplit(".", 1)
        module = importlib.import_module(model_path)
        clazz = getattr(module, clazz_name)
        method = getattr(clazz, clazz_info[1])
        HookerBase.STATIC_METHODS[path] = method     # 缓存
        return method


class HookerOne(HookerBase):
    """普通（同步执行，触发者进行执行"""

    def send(self, type_, data):
        """触发事件，由触发者线程调用"""
        self.logger.debug('{} SendEvent'.format(self.count))
        self.__event_process__(type_, data)
        self.count_add()


class EventManager(HookerBase):
    """ 工作方式二：单线程异步处理 """

    def __init__(self):
        super().__init__()
        self._queue = Queue(maxsize=215)            # 事件数量列表
        self.__thread = threading.Thread(target=self.__run)   # 事件处理线程

    def __run(self):
        """线程运行函数"""
        self.logger.debug('{} run'.format(self.count))
        while self.__active or self._queue.empty() is False:
            item = None
            try:
                item = self._queue.get(timeout=self.QUEUE_TIMEOUT)  # 获取事件的阻塞时间设为1秒
                self.__event_process__(item['type'], item['data'])

            except Empty:
                pass
            except BaseException as e:
                self.logger.exception("hooker 回调异常")
            finally:
                if item is not None: self._queue.task_done()        # 得到了的任务就要完成任务，不管是否异常

        self.logger.debug('{} Stop Complete, qsize={}'.format(self.count, self._queue.qsize()))

    def start(self):
        """启动"""
        self.logger.debug('{} Start'.format(self.count))
        self.__active = True        # 将事件管理器设为启动
        self.__thread.start()       # 启动事件处理线程
        self.count_add()
        return self

    def join(self):
        self.__active = False       # 将事件管理器设为停止
        self._queue.join()
        self.__thread.join()        # 等待事件处理线程退出
        self.count_add()

    def stop(self):
        """停止"""
        self.logger.debug('{} Stop, qsize={}'.format(self.count, self._queue.qsize()))
        self.join()
        self.count_add()

    def send(self, type_, data=None):
        """发送事件，向事件队列中存入事件"""
        self.logger.debug('{} SendEvent'.format(self.count))
        self._queue.put({'type': type_, 'data': data})
        self.count_add()


class ThreadPoolHooker(HookerBase):
    """
    工作方式三：多线程异步处理
    1. 业务中确保操作的数据对象，保证只能一个流程一个流程操作，或支持多线程同时操作该数据对象；
    2.
    """
    THR_COUNT = 4

    def __init__(self):
        super().__init__()
        self._queue = Queue(maxsize=512)            # 任务队列
        self.__poolExecutor = ThreadPoolExecutor(max_workers=ThreadPoolHooker.THR_COUNT)   # 线程池

    def __run(self):
        thr_id = threading.current_thread().ident
        self.logger.debug('hooker_{},  run'.format(thr_id))
        # 循环监听
        while self._active or self._queue.empty() is False:
            self.logger.debug("self.__active, self._queue.empty() {}, {}".format(self._active, self._queue.empty() is False))
            item = None
            try:
                item = self._queue.get(timeout=self.QUEUE_TIMEOUT)  # 获取事件的阻塞时间设为1秒
                self.__event_process__(item['type'], item['data'])

            except Empty:
                pass
            except BaseException as e:
                self.logger.exception("hooker_{}回调异常\ninfo={}".format(thr_id, item))
            finally:
                if item is not None:
                    self.logger.debug('完成一个任务 {}'.format(item))
                    self._queue.task_done()
                item = None

        self.logger.debug('hooker_{}, {} Stop Complete, qsize={}'.format(thr_id, self.count, self._queue.qsize()))

    def start(self):
        """启动"""
        if self._active:
            return
        self.logger.debug('{} Start'.format(self.count))
        self._active = True        # 将事件管理器设为启动
        for idx in range(self.THR_COUNT):   # 添加并启动任务
            self.__poolExecutor.submit(self.__run)
        self.count_add()
        return self

    def join(self):
        """等待执行完成"""
        self.logger.debug('{} Join, qsize={}'.format(self.count, self._queue.qsize()))
        self._queue.join()          # 等待队列全部完成
        self.count_add()

    def stop(self):
        """停止"""
        self.logger.debug('{} Stop, qsize={}'.format(self.count, self._queue.qsize()))
        if self._active is False: return self.logger.debug('队列未激活')
        while self._queue.qsize() > 0:
            self.logger.debug("等待任务队列清空")
            time.sleep(self.QUEUE_TIMEOUT)
        self._active = False       # 将事件管理器设为停止
        self.join()
        self.__poolExecutor.shutdown()  # 等待线程池结束
        self.count_add()

    def send(self, type_, data=None):
        """触发事件"""
        self.logger.debug('{} SendEvent'.format(self.count))
        self._queue.put({'type': type_, 'data': data})
        self.count_add()


# 全局单例
# hooker = Hooker()       # 同步执行
# hooker = EventManager()     # 异步执行（单线程
hooker = ThreadPoolHooker()     # 默认hooker（异步执行（多线程