"""

"""
import inspect
from .utils import ClassUtils, BaseClass

# 判断环境释放安装依赖
INSTALL_DPS = True
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.base import STATE_RUNNING
except:
    INSTALL_DPS = False


class Scheduler(BaseClass):
    _INDEX_ = 0
    _TASKS_ = {}

    def initialize(self, tasks=None):
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        for k, v in ([] if tasks is None else tasks):
            self._add(v, k)

    def start(self):
        if self.scheduler.state != STATE_RUNNING:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.state == STATE_RUNNING:
            self.scheduler.shutdown()

    def __load_app__(self, path):
        """加载APP下定时器"""

    def _load_func(self, tar):
        """用户方法加载"""
        if inspect.isfunction(tar):
            return tar
        elif isinstance(tar, str):
            return ClassUtils.load_method(tar)
        else:
            raise Exception("不支持得方法表达式")

    def add(self, cron, func=None, id_=None):
        if isinstance(cron, list):
            for it in cron:
                self._add(it['cron'], self._load_func(it['func']))
        else:
            self._add(cron, self._load_func(func), id_)

    def _add(self, cron, func, id_=None):
        if INSTALL_DPS is False:
            raise Exception("'apscheduler' dependencies are not installed")

        ka = str(cron).split(" ")
        if len(ka) != 7:
            raise ValueError('Error cron expression; got {}, expected 7, ={}'.format(len(ka), cron))

        self._INDEX_ += 1
        id_ = "TASK_{}".format(self._INDEX_) if id_ is None else id_
        if id_ in self._TASKS_:
            raise Exception("任务id已存在，id={}".format(id_))

        max_instances = 30      # 最大同时任务
        self.scheduler.add_job(func, 'cron', second=ka[0], minute=ka[1], hour=ka[2], day=ka[3], month=ka[4],
                               day_of_week=ka[5], year=ka[6], id=id_, max_instances=max_instances)
