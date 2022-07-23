"""
    模型关联
"""
from .func import *
from ..log import get_logger
logger = get_logger()


class RelationModel:
    type_ = None

    def __init__(self, *args, **kwargs):
        # 关联模型名称，该模型应该和对应模型在同一目录，否则应该写全路径，支出表名查找模型
        self.relation_name = args[0]    # type:quickpython.database.model
        self.relation_key = kwargs.pop('relation_key', None)    # 关联模型字段
        self.local_key = kwargs.pop('local_key', None)          # 当前模型字段
        self.eagerly_type = kwargs.pop('eagerly_type', 0)       # 预载入方式 0 -JOIN 1 -IN
        self.model = None
        self.model_cls = None
        self.is_load_data = False
        self.name = None        # 父模型关联字段名称、本类对应的属性名称
        self.parent = None    # 父模型对象
        self.local_key_val = None    # 父模型关联字段名称、本类对应的属性名称
        # 基础查询器
        self.__query = None     # QuerySet().table()

    def load_model_cls(self, parent):
        """获取对应模型并进行查询-到调用此方法说明是单独调用的"""
        if self.model is not None:
            return self.model
        # 父模型的关联字段
        if self.local_key is None:
            self.local_key = "{}_id".format(self.name)

        self.parent = parent
        if hasattr(parent, self.local_key) is False:
            raise Exception("未找到父模型的关联字段 {}".format(self.local_key))

        # 获取关联模型类
        cls_path = "{}.{}".format(parent.__class__.__module__, self.relation_name)
        self.model_cls = load_cls(cls_path)
        if self.model_cls.__table_pk__ is None:
            self.model_cls()

        if self.relation_key is None:
            self.relation_key = self.model_cls.__table_pk__.name

        return self.model

    def bind_parent_where(self):
        self.local_key_val = getattr(self.parent, self.local_key)
        if self.local_key_val is None:
            raise Exception("父模型关联属性值为空")
            logger.warning("父模型关联属性值为空 {}".format(self.local_key))

        self.model = self.model_cls()
        self.model.__relation__ = self
        self.model.where(self.relation_key, '=', self.local_key_val)

    def __load_data__(self):
        if self.is_load_data:
            return self.model

        self.is_load_data = True
        self.bind_parent_where()

        if isinstance(self, OneToOne):
            self.model = self.model.find()
            # logger.debug('self.model.__modified_fields__={}'.format(self.model.__modified_fields__))

        elif isinstance(self, OneToMany):
            self.model = self.model.select()

        return self.model

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def eagerly(self, query):
        """预载入关联查询（JOIN方式）"""
        relation = self.name
        # 处理父查询本字段，排除掉
        # 再父查询追加本模型的预载入查询
        join_table = self.model_cls.__table__
        join_alias = relation
        local_table = self.parent.__table__
        # field
        query.field(True, False, join_table, join_alias, relation + "__")
        # join
        join_on = "{}.{}={}.{}".format(local_table, self.local_key, join_alias, self.relation_key)
        query.join({join_table: join_alias}, join_on, 'LEFT')

    def withs_result_set(self, result_set):
        """预载入关联查询（数据集、多个）"""
        relation = self.name
        if self.eagerly_type == 0:
            for idx, result in result_set:
                self.match(relation, result)

    def withs_result(self, result):
        """预载入关联查询（数据、单个）"""
        relation = self.name
        if self.eagerly_type == 0:
            self.match(relation, result)

    def match(self, relation, result):
        """一对一 关联模型预查询拼装"""
        data = {relation: {}}
        for key, val in result.items():  # type:str, dict
            if key.find("__") > -1:
                name, attr = key.split("__")
                if name == relation:
                    data[name][attr] = val

        if not_empty(data[relation]):
            relation_model = self.model_cls(**data[relation])
            relation_model.__modified_fields__ = []
            relation_model.parent = self.parent     # 假设
        else:
            relation_model = None

        self.bind_parent_where()
        self.is_load_data = True
        self.model = relation_model
        self.parent.__setattr__(self.name, self.model, True)
        # logger.debug("数据装载完成：{}:{}".format(id(self.model), self.model))
        # parent_relation = getattr(self.parent, self.name)
        # logger.debug("数据装载完成-父属性值：{}:{}".format(id(parent_relation), parent_relation))


class OneToOne(RelationModel):
    type_ = "OneToOne"


class OneToMany(RelationModel):
    type_ = "OneToMany"


class HasManyThrough(RelationModel):
    type_ = "HasManyThrough"
