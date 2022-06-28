"""
model demo
"""
import logging
from app.common.models import *
from libs.utils import Utils

logger = logging.getLogger(__name__)


class DemoModel:

    def call(self):
        """"""
        self.base()
        # self.join()

    def base(self):
        # self.save()
        # self.remove()
        # self.save_update()
        # self.get()
        self.aggregation()
        # self.field_use()

    def join(self):
        self.join_1()
        # self.join_2()

    def save(self):
        """新增"""
        mtime = Utils.mtime()
        UserModel(**{'username': "test1"}).save()
        UserModel(**{'username': "test2"}).save()
        UserModel(**{'username': "test3"}).save()
        UserModel(**{'username': "test4"}).save()
        UserModel(**{'username': "test5"}).save()
        logger.info("新增耗时 {}ms".format(Utils.mtime() - mtime))

    def remove(self):
        """删除"""
        user_2 = UserModel().where(UserModel.username == "test2").find()
        if user_2 is None:
            raise Exception("未找到nickname = test2 的数据")
        else:
            user_2.remove()
        logger.info("删除成功")

    def save_update(self):
        """更新"""
        user_3 = UserModel().where(UserModel.username == "test3").find()
        if user_3 is None:
            raise Exception("未找到nickname = test3 的数据")
        else:
            user_3.nickname = user_3.username
            user_3.save()
        logger.info("更新成功")

    def get(self):
        """查询"""
        # user_4 = UserModel().where(UserModel.username == "lo106258").get()
        # if user_4 is None: raise Exception("未找到nickname = test4 的数据")
        # logger.info("user_4={}".format(user_4))
        # 参数条件查询
        # user_5 = UserModel().where(username="lo106258").get()
        # if user_5 is None: raise Exception("未找到user_5数据")
        # logger.info("user_5={}".format(user_5))

        # 包含标签
        user_5_2 = UserModel().where(id__in=["40830", "40831"]).select()
        if user_5_2 is None: raise Exception("未找到 user_5_2 数据")
        logger.info("user_5_2={}".format(user_5_2))
        user_5_3 = UserModel().where(id__not_in=["40830", "40831"]).select()
        if user_5_3 is None: raise Exception("未找到 user_5_3 数据")
        logger.info("user_5_3={}".format(user_5_3))

        # 比较标签
        # for it in "eq,neq,gt,egt,lt,elt".split(','):
        #     field = "id__" + it
        #     user_5_4 = UserModel().where(**{field: 40830}).select()
        #     if user_5_4 is None:
        #         raise Exception("未找到 条件{}的 user_5_4 数据".format(field))
        #     logger.info("user_5_4={}".format(user_5_4))

        # 多条
        # user_rows = UserModel().where(UserModel.username == "test4").select()
        # logger.info("user_rows={}:{}".format(len(user_rows), user_rows))
        # logger.info("查找成功")

    def aggregation(self):
        ret = UserModel().where(id__in=["40830", "40831"]).aggregation("SUM(id) sum_id")
        logger.info("ret={}".format(ret))
        ret = UserModel().group("branch_id").aggregation("COUNT(id) count_id")
        logger.info("ret2={}".format(ret))

    def field_use(self):
        """字段使用和参与计算"""
        user_5 = UserModel().where(UserModel.username == "test5").find()
        if user_5 is None:
            logger.info("未找到的数据")

        logger.info("修改前 user.school_id={}".format(user_5.school_id))
        user_5.school_id = user_5.school_id + 1
        logger.info("修改后 user.school_id={}".format(user_5.school_id))
        user_5.save()
        logger.info("保存后 user_5={}".format(user_5))

    def join_1(self):
        """模型预载入查询单条 一对一（left join）"""

        # 预加载
        # user_6 = UserModel().withs([UserModel.device])\
        #     .where("user.id", 40830)\
        #     .find()
        # Utils.print_dicts(user_6)
        # Utils.print_dicts(user_6.device)

        # 懒加载
        # user_6 = UserModel().where("user.id", 40830).get()
        # Utils.print_dicts(user_6)
        # print("user_6.device", id(user_6.device), user_6.device)
        # print("user_6.device", id(user_6.device), user_6.device)
        # user_6.device.key = Utils.datetime_now()
        # user_6.device.save()
        # print("user_6.device", id(user_6.device), user_6.device)

        # print("user_6.device", user_6.device.__query__.get_map())
        # user_6.device.save()
        # logger.debug("user_6.device={}".format(user_6.device))
        # logger.debug("user_6.device={}".format(user_6.device.where('platform', 2).get()))
        # logger.debug("user_6.school={}".format(user_6.school))

        # logger.debug("user_6.money_log={}".format(user_6.money_log))
        # money_log = user_6.money_log.order('id', 'DESC').limit(10).select()
        # logger.debug("user_6.money_log={}:{}".format(len(money_log), money_log))
        # Utils.print_dicts(user_6)
        # Utils.print_dicts(user_6.device)

    def join_2(self):
        """模型预载入查询 多个"""
        user_7 = UserModel().withs([UserModel.device, UserModel.school])\
            .where(UserModel.id == 40850)\
            .where(UserModel.branch_id == 1062)\
            .select()
        logger.debug("user_7=\n{}".format(Utils.dict_to_str(user_7)))

    def tran(self):
        try:
            QuerySet.start_trans()      # TODO::开启事务
            """
                执行数据操作
            """
            QuerySet.commit()       # TODO::提交事务

        except BaseException as exc:
            QuerySet.rollback()     # TODO::回滚事务
            raise exc


if __name__ == '__main__':
    try:
        DemoModel().call()
    except:
        Utils.print_exc()
