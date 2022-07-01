"""
    模型基类
"""

import logging, copy
from .query import QuerySet
from .contain.func import *
from .contain.columns import *
from .contain.relation import *
from .contain.pagination import Pagination


logger = logging.getLogger(__name__)


class Model:
    """模型基类"""
    __table__ = None        # 模型对象数据表表名
    __table_pk__ = None     # type:ColumnBase
    __table_args__ = None   # 表加参数
    __table_fields__ = None # 模型的字段列表
    __attrs__ = None        # 模型显示的属性
    __soft_delete__ = None  # type:ColumnBase
    __relation__ = None     # 被关联信息
    __parent__ = []         # 父模型
    __origin__ = {}         # 原始数据（数据查询
    __data__ = {}           # 设置的数据
    __withs__ = []          # 预加载属性
    __query__ = QuerySet()  # type:QuerySet

    def __init__(self, *args, **kwargs):
        self._is_new = False  # 是否是新增
        self.__modified_fields__ = []  # 模型数据是否修改，用于更新
        self.__relation__ = None    # 关联模型属性
        self.__withs__ = []         # 预加载属性
        self._load_field()          # 初始化字段信息
        # 对象数据初始化
        for key in self.__attrs__:
            if key in kwargs:
                setattr(self, key, kwargs.pop(key))
            else:
                cls_attr = object.__getattribute__(self.__class__, key)
                setattr(self, key, copy.copy(cls_attr))
        # 查询器
        self.__query__ = QuerySet().table(self.__table__)   # type:QuerySet

    def _load_field(self):
        self.__class__._get_cls_fields()

    @property
    def name(self):
        return self.__class__.__name__

    @classmethod
    def _get_cls_fields(cls):
        if cls.__table_fields__ is not None:
            return
        cls.__table_fields__ = {}
        cls.__attrs__ = {}
        cls_dict = dict(cls.__dict__)
        for name in cls_dict:
            if str(name).find("__") == 0:
                continue
            # obj = getattr(cls, name)
            obj = cls.__getattribute__(cls, name, True)
            if isfunction(obj):
                continue
            if isinstance(obj, ColumnBase):
                # logger.debug("加载模型字段 cls={}, name={}, obj={}".format(cls, name, obj))
                obj.name = name
                if obj.primary_key:
                    # logger.debug("设置主键 {}={}:{}".format(name, type(obj), obj))
                    cls.__table_pk__ = obj
                cls.__table_fields__[name] = obj
                cls.__attrs__[name] = obj
                # 软删除字段：只能存在一个
                if obj.soft:
                    cls.__soft_delete__ = obj

            if issubclass(obj.__class__, RelationModel):
                obj.name = name
                cls.__attrs__[name] = obj

        # logger.debug("加载模型字段 cls={}, primary_key={}".format(cls, cls.__table_pk__))

    def where(self, *args, **kwargs):
        args = list(args)
        where = {'key': None, 'type': '=', 'val': None}
        # 字典查询条件: id__eq、id__in
        if len(kwargs) > 0:
            for it, val in kwargs.items():
                if it.find('__') > -1:
                    if empty(val):
                        return self
                    it_arr = it.split('__')
                    self.__query__ = self.__query__.where({it_arr[0]: [it_arr[1], val]})
                else:
                    self.__query__ = self.__query__.where(it, "=", val)
            return self
        elif len(args) > 0 and isinstance(args[0], ColumnCmp):
            where = args[0].__dict__()
        elif len(args) == 1 and isinstance(args[0], dict):
            self.__query__ = self.__query__.where(args[0])
            return self
        else:
            where['key'] = args[0]
            if len(args) == 2:
                where['val'] = args[1]
            elif len(args) == 3:
                where['type'] = args[1]
                where['val'] = args[2]

        if len(self.__withs__) > 0 and len(args) >= 2 and where['key'].find(".") == -1:
            where['key'] = self.__table__ + "." + where['key']

        self.__query__ = self.__query__.where(where['key'], where['type'], where['val'])
        return self

    def get(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and args[0] is not None:
            self.where(**{self.__table_pk__.name: args[0]})
        elif len(kwargs) > 0:
            self.where(*args, **kwargs)
        return self.find()

    def find(self):
        # 预加载处理（预载入模式开启后，数据返回将进行关联数据填充
        if not_empty(self.__withs__):
            # 加载本表字段
            self.__query__.field(True, False, self.__table__)
            # 处理关联表
            for it in self.__withs__:
                it.load_model_cls(self)
                it.eagerly(self.__query__)

        # 执行查询
        row = self.__query__.find()
        if row is None:
            return None

        # 数据装载
        obj_data = {}
        for key in self.__table_fields__:
            if key in row:
                obj_data[key] = row[key]

        # obj = object.__new__(self.__class__)  # 另外一种模型new方法
        # obj.__init__()
        obj = self.__class__(**obj_data)
        obj.__relation__ = self.__relation__
        obj.__modified_fields__ = []

        # 预载入结果
        if not_empty(self.__withs__):
            obj.eagerly_result(row, self.__withs__)

        return obj

    def all(self):
        logger.warning("此方法为兼容而存在")
        return self.select()

    def select(self):
        # 预加载处理（预载入模式开启后，数据返回将进行关联数据填充
        if not_empty(self.__withs__):
            # 加载本表字段
            self.__query__.field(True, False, self.__table__)
            # 处理关联表
            for it in self.__withs__:
                it.load_model_cls(self)
                it.eagerly(self.__query__)

        # 执行查询
        rows = self.__query__.select()
        if empty(rows):
            return []

        # 数据装载
        ret = []
        for row in rows:
            obj_data = {}
            for key in self.__table_fields__:
                if key in row:
                    obj_data[key] = row[key]

            obj = self.__class__(**row)
            obj.__relation__ = self.__relation__
            obj.__modified_fields__ = []
            ret.append(obj)
            # 预载入结果
            if not_empty(self.__withs__):
                obj.eagerly_result(row, self.__withs__)

        # logger.debug("ret={}".format(ret))
        return ret

    def __query___soft_delete(self):
        """追加软删除列查询条件"""
        # self.__query__.where({})
        return self

    def save(self, data=None):
        # 赋值
        self.__load_data(data)

        if self.__is_modified__() is False:
            return

        """
        获取修改列的值，获取到的值经过__getattribute__处理会是直接的基本数据类型
        """
        update_data = {key: getattr(self, key) for key in self.__modified_fields__}

        # 新增还是更新
        pk = self.__class__.__table_pk__
        if pk is None or pk.name is None:
            raise Exception("模型ORM不支持没有主键的model.save操作")

        pk_val = getattr(self, pk.name)
        if pk_val is None:
            # 新增还涉及默认数据的列：default、insert_default、update_default
            for name, col in self.__class__.__table_fields__.items():
                if col.has_insert_default() and (name not in update_data or update_data[name] is None):
                    update_data[name] = col.__get_insert_default__()

            update_data = self.__data_sort(update_data)
            pk_val = self.__query__.insert_get_id(update_data)      # 执行插入
            # logger.debug("主键值={}".format(pk_val))
            setattr(self, pk.name, pk_val)

        else:
            # 更新涉及的数据列：update_default
            for name, col in self.__class__.__table_fields__.items():
                if col.has_update_default() and (name not in update_data or update_data[name] is None):
                    update_data[name] = col.__get_update_default__()

            self.where(pk == pk_val)
            update_data = self.__data_sort(update_data)
            self.__query__.update(update_data)

        self.__modified_fields__ = []
        return 1

    def remove(self):
        """模型删除方法"""
        if len(self.__query__.get_map()) == 0:
            pk, pk_val = self.__get_pk_val__()
            self.where(pk == pk_val)
        # 软删除
        if self.__soft_delete__ is not None:
            if isinstance(self.__soft_delete__, Datetime):
                return self.__query__.save({self.__soft_delete__.name: ColumnFunc.now()})  # 软删除
            else:
                raise Exception("不支持的软删除字段类型")
        return self.__query__.delete()

    def __get_pk_val__(self):
        pk = self.__class__.__table_pk__
        return pk, None if pk is None else getattr(self, pk.name)

    def __data_sort(self, data):
        """数据根据字段顺序排序"""
        data2 = {}
        for col_name, col in self.__class__.__table_fields__.items():
            for it, val in data.items():
                if col_name == it:
                    data2[col_name] = val
        return data2

    """
        批量方法
    """
    def update(self, data):
        # 是否未加载就保存，那就先查询
        if self.__is_load() and len(self.__query__.get_map()) > 0:
            self.__query__.update(data)

    def delete(self):
        if self.__is_load() and len(self.__query__.get_map()) > 0:
           self.__query__.delete()     # 实际删除

    def aggregation(self, *args):
        return self.__query__.aggregation(*args)

    """
        属性控制
    """
    def __is_modified__(self):
        return len(self.__modified_fields__) > 0

    def __is_load(self):
        return self.__get_pk_val__() is not None

    def __load_data(self, data):
        if data is not None:
            for key in data:
                if key in self.__attrs__:
                    self.__setattr__(key, data[key])

    def __setattr__(self, name: str, value, attr_direct=False):
        # logger.debug("__setattr__ {}:{}".format(id(self), key))
        if name.find("_") == 0:
            return object.__setattr__(self, name, value)

        if attr_direct is False:        # 非直接操作，就加载下数据
            self.__relation_load_data()
            self.__modified_fields__.append(name)

        object.__setattr__(self, name, value)
        # logger.debug("__setattr__ ok {}:{}".format(id(self), key))

    def __getattr__(self, name):
        # 在model上未找到的属性，到
        # print("在model上未找到的属性", name)
        if hasattr(self.__query__, name):

            def proxy_method(*args, **kwargs):
                method = getattr(self.__query__, name)
                ret = method(*args, **kwargs)
                # print("代理方法-执行结果", method, ret)
                if isinstance(ret, QuerySet):
                    self.__query__ = ret
                    return self
                return ret

            return proxy_method

        # raise Exception("未在模型对象{}上找到名为'{}'的属性或方法".format(self.name, name))
        return None

    def __getattribute__(self, attr_name, attr_direct=False):
        attr = object.__getattribute__(self, attr_name)
        if attr_name.find("_") == 0 or attr_direct:     # 自带属性直接返回
            return attr
        if isinstance(attr, types.MethodType):              # 方法直接返回
            return attr

        # logger.debug("{}=>{}:{}".format(property_name, type(attr), attr))

        # 下级属性是关联模型
        self.__relation_load_data()
        attr = object.__getattribute__(self, attr_name)

        if iscolumn(attr.__class__):
            return attr.value

        if issubclass(attr.__class__, RelationModel):
            # logger.debug("关联模型属性")
            attr.load_model_cls(self)
            attr.bind_parent_where()
            object.__setattr__(self, attr_name, attr.model)
            # logger.debug("关联模型属性 返回新的模型={}".format(id(attr.model)))
            # logger.debug("关联模型属性 返回新的模型={}".format(type(attr.model)))
            # logger.debug("关联模型属性 返回新的模型={}".format(attr.model.__relation__))
            return attr.model

        return attr

    def __str__(self):
        pk, pk_val = self.__get_pk_val__()
        return "{} object({})=>{}".format(self.__class__.__name__, pk_val, self.__dict__())

    # def __repr__(self):
    #     return self.__str__()

    def __dict__(self):
        data = {}
        withs_name = [it.name for it in self.__withs__]
        for k, c in self.__attrs__.items():     # 只输出指定字段
            if len(withs_name) > 0 and isinstance(c, RelationModel):  # 关联对象数据
                if k in withs_name:
                    data[k] = getattr(self, k)
            else:
                data[k] = getattr(self, k)

        return data

    def __getstate__(self):
        return self.__dict__()

    def __setstate__(self, state):
        self.__init__()
        self.__load_data(state)

    def to_dict(self):
        if isinstance(self, list):
            return [it.__dict__() for it in self]
        return self.__dict__()

    """
    预加载方法
    """
    def withs(self, models):
        """标记预加载"""
        if empty(models):
            return self

        if isinstance(models, str):
            models = models.split(',')

        for it in models:
            if isinstance(it, OneToOne):    # 只支持一对一的预载入
                self.__withs__.append(it)

        return self

    def eagerly_result(self, result, withs):
        """装载数据"""
        self.__withs__ = withs
        # 关联数据载入
        for it in self.__withs__:
            item = object.__getattribute__(self, it.name)
            item.load_model_cls(self)
            item.withs_result(result)

    def __relation_load_data(self):
        """关联模型加载数据"""
        __relation__ = object.__getattribute__(self, '__relation__')
        if __relation__ is not None and __relation__.is_load_data is False:
            if isinstance(__relation__, OneToOne):     # 只懒加载一对一
                data = __relation__.__load_data__()
                if isinstance(data, self.__class__):
                    for key in self.__attrs__:
                        self.__setattr__(key, getattr(data, key), True)
                    self.__modified_fields__ = []       # 可能由于顺序问题
                    # setattr(__relation__.parent, __relation__.name, self)       # 保持本对象
                elif isinstance(data, list):
                    setattr(__relation__.parent, __relation__.name, data)

    """
    扩展方法
    """
    def paginate(self, page=None, page_size=None, params=None, select_related=True):
        """分页整理查询"""
        page = 1 if page is None else page
        page_size = 1 if page_size is None else page_size
        page_size = page_size if 0 < page_size < 1000 else 20
        # 关联的属性
        if select_related:
            related_attrs = [it for it in self.__attrs__ if isinstance(it, RelationModel)]
            self.withs(related_attrs)
        # 查询
        total = self.__query__.count()
        rows = self.__query__.page(page, page_size).select()
        return Pagination(rows, page, page_size, total, params)


