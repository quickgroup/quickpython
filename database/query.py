"""
    查询基础操作集合
    环境：pymysql>=1.0.2
"""
import pymysql
import time, math, re
from .connector.connection import Connection
from .contain.func import *
from .contain.extend import *
from . import settings
from .log import get_logger
logger = get_logger()

options = settings.DATABASES['default']['options']
def_name = 'default'


def format_field(name):
    if name is None or len(name) == 0:
        return name
    if options['field_sep'] is None or options['field_sep'] is True:
        arr = name.split(".")
        return "`{}`".format(name) if len(arr) == 1 else "`{}`.`{}`".format(arr[0], arr[1])
    return name


def format_val(val):
    if val is None:
        ret = 'NULL'
    elif isinstance(val, int):
        ret = str(val)
    elif isinstance(val, float):
        ret = str(val)
    else:
        val = pymysql.converters.escape_string(str(val))        # 特殊符号转义，防止SQL注入
        ret = '{}{}{}'.format(options['val_str_sep'], val, options['val_str_sep'])

    return ret


def typeof(variate):
    mold = None
    if isinstance(variate, int):
        mold = "int"
    elif isinstance(variate, str):
        mold = "str"
    elif isinstance(variate, float):
        mold = "float"
    elif isinstance(variate, list):
        mold = "list"
    elif isinstance(variate, tuple):
        mold = "tuple"
    elif isinstance(variate, dict):
        mold = "dict"
    elif isinstance(variate, set):
        mold = "set"
    return mold


class Transaction:

    def __init__(self, name='default'):
        self.conn = Connection.connect(name)

    def __enter__(self):
        self.conn.start_trans()

    def __exit__(self, exc_type, value, traceback):
        if exc_type is None:
            self.conn.commit()
            return True
        else:
            self.conn.rollback()
            return False


class QuerySet(object):

    def __init__(self, connection=None):
        self.__map = {}
        self.__table = ''
        self.__fields__ = []
        self.__where = {}
        self.__alias = ''
        self.__join = []
        self.__having = []
        self.__distinct = False
        self.__for_update = None
        self.__fetch_sql__ = False
        self.__options = {
            'multi': {},
            'where': {},
        }
        self._conn = self.connect() if connection is None else connection
        self.prefix = self._conn.get_config("prefix", '')
        self.__database = self._conn.get_config('database', '')

    @staticmethod
    def connect():
        return Connection.connect('default')
    
    def __conn__(self):
        return self._conn

    def __close(self):
        self.__conn__().close()

    @property
    def __table__(self):
        """完整表名（带前缀）"""
        return self.__table if self.prefix is None else self.prefix + self.__table

    def table(self, table):
        self.__table = table
        return self

    def __table_name_sql__(self):
        """sql中的表名，识别并增加别名"""
        if empty(self.prefix):
            return format_field(self.__table__)
        table_name = "{}{}".format(format_field(self.__table__), format_field(self.__table))
        return table_name

    def where(self, field, op=None, condition=None):
        self.__parse_where_exp("AND", field, op, condition)
        return self

    def where_raw(self, field):
        self.__parse_where_exp("AND", field, op=None, condition=None)
        return self

    def __parse_where_exp(self, logic, field, op, condition, param=None, strict=False):
        logic = logic.upper()
        param = [] if param is None else param
        where = {}
        # logic
        if logic not in self.__map:
            self.__map[logic] = {}

        # 匿名方法
        if isfunction(field):
            field(self)
        # 自写语句
        elif isinstance(field, str) and len(re.findall('[,=\>\<\'\"\(\s]', field)) > 0:
            field = Expression(field)
            self.__map[logic][str(field)] = ['exp', field]
        # 条件组装
        elif op is None and condition is None:
            if isinstance(field, dict):
                where = field
                for k, val in field.items():
                    if isinstance(val, list):
                        self.__map[logic][k] = val
                    else:
                        self.__map[logic][k] = ['=', val]

            elif isinstance(field, str):
                where[field] = ['null', '']
                self.__map[logic][field] = where[field]

        elif empty(condition):
            where[field] = ['=', op]
            self.__map[logic][field] = where[field]
        else:
            if op == 'exp':
                where[field] = ['exp', Expression(condition)]
            else:
                where[field] = [op, condition]
            self.__map[logic][field] = where[field]

        if len(where) > 0:
            if logic not in self.__options['where']:
                self.__options['where'][logic] = {}

    def limit(self, start=0, limit=None):
        if limit is None:
            limit = start
            start = 0
        self.__options['limit'] = "{}, {}".format(start, limit)
        return self

    def page(self, page=1, page_size=20):
        self.limit((page - 1) * page_size, page_size)
        return self

    def order(self, field, asc='ASC'):
        if not_empty(field):
            if 'order' not in self.__options:
                self.__options['order'] = []
            self.__options['order'].append("{} {}".format(format_field(field), asc.upper()))
        return self

    def group(self, group):
        self.__options['group'] = group
        return self

    def field(self, field, is_except=False, table_name=None, prefix=None, alias=None):
        if empty(field):
            return self

        def array_diff(arr, arr2):
            return arr      # 用的排除

        if field is True:
            fields = self.__get_column__(list, self.__table__ if table_name is None else table_name)
            field = ['*'] if fields is None else fields
        elif is_except:
            fields = self.__get_column__(list, self.__table__ if table_name is None else table_name)
            field = field if fields is None else array_diff(fields, field)

        if not_empty(table_name):
            prefix = table_name if prefix is None else prefix
            for idx in range(len(field)):
                val = field[idx]
                val = "{}.{}{}".format(prefix, val, ('' if alias is None else " AS {}{}".format(alias, val)))
                field[idx] = val

        self.__fields__.extend(field)
        return self

    def distinct(self, is_true=True):
        self.__distinct = is_true
        return self

    def having(self, where):
        self.__having.append(where)
        return self

    __op_map = {
        'EQ': '=',
        'NEQ': '<>',
        'LT': '<',
        'LTE': '<=',
        'GT': '>',
        'GTE': '>=',
    }

    __op_in = {
        'IN': 'IN',
        'NOT IN': 'NOT IN',
        'NOT_IN': 'NOT IN',
        'EXISTS': 'EXISTS',
    }

    __op_extend = {
        'RANGE': 'RANGE',
    }

    def __get_map__(self):
        return self.__map

    def __set_map__(self, map):
        self.__map = map
        return self

    def __com_where_sql(self, to_str=True):
        """构建WHERE条件"""
        # logger.debug("self.__map={}".format(self.__map))
        sa = []
        for logic, items in self.__map.items():
            if len(items) == 0:
                continue
            sa_where = []
            for field, condition in items.items():
                # logger.debug("condition={}".format(condition))
                conditions = condition if isinstance(condition[0], list) else [condition]
                for cond in conditions:
                    op = str(cond[0]).upper()
                    if op == 'EXP':
                        where_item = str(cond[1])      # 表达式查询，支持SQL语法
                    elif op in self.__op_map:
                        where_item = "{}{}{}".format(format_field(field), self.__op_map[op], format_val(cond[1]))
                    elif op in self.__op_in:
                        in_val = cond[1]
                        if isinstance(cond[1], list):
                            in_val = [format_val(it) for it in cond[1]]
                            in_val = ",".join(in_val)
                        where_item = "{}{}({})".format(format_field(field), self.__op_in[op], in_val)
                    elif op in self.__op_extend:
                        if op == 'RANGE':
                            val = cond[1]
                            where_item = "{} BETWEEN {} AND {}".format(format_field(field), format_val(val[0]), format_val(val[1]))
                    else:
                        where_item = "{}{}{}".format(format_field(field), cond[0], format_val(cond[1]))

                    sa_where.append(where_item)

            if len(sa) > 0:
                sa.append(logic)  # 前面有条件了，追加本次的条件
            if len(sa_where) > 0:
                sa.append(" {} ".format(logic).join(sa_where))

        if len(sa) == 0:
            return ""
        sa.insert(0, "WHERE")
        return " ".join(sa) if to_str else sa

    def __com_query_sql(self):
        """公共查询SQL"""
        if self.__table__ is None:
            return None

        sa = ["SELECT"]
        if self.__distinct:
            sa.append("distinct")

        fields = ','.join(self.__fields__)
        sa.append("{}".format(fields if len(fields) > 0 else '*'))
        sa.append("FROM {}".format(self.__table_name_sql__()))
        if not_empty(self.__alias):
            sa.append(self.__alias)

        if not_empty(self.__join):
            for item in self.__join:
                table, alias = item['table'], ''
                if isinstance(table, dict):
                    for key in table:
                        table, alias = key, table[key]
                table = self.__complement_table_name(table)
                sa.append("{} JOIN {} {} ON {}".format(item['type_'], table, alias, item['on']))

        if not_empty(self.__map):
            sa.append(self.__com_where_sql())

        if 'group' in self.__options:
            sa.append("GROUP BY {}".format(self.__options['group']))

        if len(self.__having) > 0:
            for item in self.__having:
                sa.append(item)

        if not_empty(self.__options.get('order')):
            sa.append("ORDER BY {}".format(",".join(self.__options.get('order', []))))
        if not_empty(self.__options.get('limit')):
            sa.append("LIMIT {}".format(self.__options['limit']))
        if not_empty(self.__for_update):
            sa.append(self.__for_update)

        return " ".join(sa)

    def build_sql(self):
        column = self.__fields__
        if column == '*':
            column = self.__get_column__(str)
        sql = self.__com_query_sql()
        return sql

    def fetch_sql(self):
        self.__fetch_sql__ = True
        return self

    def __get_field(self, table=None):
        column = self.__fields__
        if '*' in column:
            column = self.__get_column__(str, table=table)

        return column

    """
    数据执行操作（调用即执行）
    """

    def find(self):
        self.limit(1)
        sql = self.__com_query_sql()
        if sql is None or len(sql) == 0:
            return None

        if self.__fetch_sql__:
            return sql
        count, result, field_info = self.__conn__().execute_all(sql)
        return None if empty(result) else result[0]

    def select(self):
        sql = self.__com_query_sql()
        if sql is None:
            return None

        if self.__fetch_sql__:
            return sql
        return self.__conn__().execute_all(sql)[1]

    def value(self, field):
        _fields = self.__fields__
        self.__fields__ = [field]
        sql = self.__com_query_sql()
        count, result, _ = self.__conn__().execute(sql)
        self.__fields__ = _fields
        return 0 if result is None else result[field]

    def count(self):
        return self.value('count(*)')

    def aggregation(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            self.__fields__.extend(str(args[0]).split(','))
        else:
            self.__fields__.extend(args)

        return self.find()

    def insert(self, data):
        if isinstance(data, dict) is False:
            return None

        fields, values = [], []
        for key, val in data.items():
            fields.append(format_field(key))
            values.append(format_val(val))

        if len(fields) == 0 or len(values) == 0:
            return 0

        sql = "INSERT INTO {}({}) VALUES({})".format(self.__table_name_sql__(), ", ".join(fields), ", ".join(values))
        if self.__fetch_sql__:
            return sql
        return self.__conn__().execute(sql)[0]

    def insert_get_id(self, data):
        if isinstance(data, dict) is False:
            return None

        fields, values = [], []
        for key, val in data.items():
            fields.append(format_field(key))
            values.append(format_val(val))

        if len(fields) == 0 or len(values) == 0:
            return 0

        sql = "INSERT INTO {}({}) VALUES({})".format(self.__table_name_sql__(), ", ".join(fields), ", ".join(values))
        if self.__fetch_sql__:
            return sql

        # 执行
        count, ret, pk = self.__conn__().execute_get_id(sql)
        # logger.debug("pk={}".format(pk))
        return pk

    def insert_all(self, datas):
        """批量新增"""
        if isinstance(datas, list) is False:
            return None
        count = 0
        # for data in datas:
        #     count += self.insert(data)
        bulk_size = int(self._conn.get_config('bulk_size'))
        bulk_count = math.ceil(len(datas) / bulk_size)

        for idx in range(bulk_count):
            fields_str, values_list = "", []
            for data in datas[idx * bulk_size : idx * bulk_size + bulk_size]:
                fields, values = [], []
                for key, val in data.items():
                    fields.append(format_field(key))
                    values.append(format_val(val))
                values_list.append("({})".format(",".join(values)))
                fields_str = ",".join(fields)

            if len(fields_str) == 0 or len(values_list) == 0:
                continue

            sql = "INSERT INTO {}({}) VALUES {}".format(self.__table_name_sql__(), fields_str, ",".join(values_list))
            if self.__fetch_sql__:
                return sql
            count += self.__conn__().execute(sql)[0]

        return count

    def update(self, data):
        if isinstance(data, dict) is False:
            return None

        if len(self.__map) == 0:
            raise Exception("禁止不使用 where 更新数据")
        where_str = self.__com_where_sql()

        fields = []
        for key, val in data.items():
            fields.append("{}={}".format(format_field(key), format_val(val)))

        if len(fields) == 0:
            return 0

        # 表名、更新的字段、限制条件
        sql = "UPDATE {} SET {} {}".format(self.__table_name_sql__(), ", ".join(fields), where_str)
        if self.__fetch_sql__:
            return sql

        return self.__conn__().execute(sql)[0]   # count, ret, _

    def set_option(self, key, val):
        return self.update({key: val})

    def delete(self):
        where_str = self.__com_where_sql()
        if len(where_str.strip()) == 0:
            raise Exception("禁止不使用 where 删除数据")

        sql = "DELETE FROM {} {}".format(self.__table_name_sql__(), where_str)
        if self.__fetch_sql__:
            return sql
        return self.__conn__().execute(sql)[0]

    def set_inc(self, key, step=1):
        return self.update({key: key + '+' + str(step)})

    def set_dec(self, key, step=1):
        return self.update({key: key + '-' + str(step)})

    def query(self, sql):
        count, ret, _ = self.__conn__().execute(sql)
        return ret

    """
    事务操作
    """
    @staticmethod
    def start_trans():
        Connection.connect(def_name).start_trans()

    @staticmethod
    def commit():
        Connection.connect(def_name).commit()

    @staticmethod
    def rollback():
        Connection.connect(def_name).rollback()

    @staticmethod
    def transaction(name=def_name):
        return Transaction(name)

    def select_for_update(self, sql="FOR UPDATE"):
        self.__for_update = sql
        return self

    def __complement_table_name(self, name:str):
        pre_len = len(self.prefix)
        if pre_len > 0:
            if name[:pre_len] != self.prefix:
                name = self.prefix + name

        return name

    def __get_column__(self, conv=None, table=None, full_name=False):
        """获取表字段"""
        table = self.__table__ if table is None else self.__complement_table_name(table)
        ck = "{}.{}_{}".format(self.__database, table, full_name)
        cache_data = self.__get_cache(ck)
        if cache_data is not None:
            count, list_data, field_info = cache_data
        else:
            sql = "SHOW FULL COLUMNS FROM `{}`".format(table)
            count, list_data, field_info = self.__conn__().execute_all(sql)
            self.__set_cache(ck, (count, list_data, field_info))

        if full_name:
            all_column = list([{'field': "{}.{} AS {}__{}".format(table, item[0], table, item[0]),
                                'field_as': "{}__{}".format(table, item[0]),
                                'field_': item[0],
                                'type': item[1], 'key': item[4]} for item in list_data])
        else:
            all_column = list([{'field': item[0],
                                'field_as': item[0],
                                'field_': item[0],
                                'type': item[1], 'key': item[4]} for item in list_data])

        if conv is str:
            return ','.join([it['field'] for it in all_column])
        if conv is list:
            return [it['field'] for it in all_column]

        return all_column

    def __get_pk__(self):
        """获取表的主键"""
        fields = self.__get_column__()
        for field in fields:
            if field["key"] == 'PRI':
                return field['field']
        return None

    """
    join查询
    """
    def join(self, table, on, type_="INNER"):
        """
        usage:  query = QuerySet().table('user')
            1.  query.join('user_info', 'user_info.user_id = user.id', 'LEFT')
            2.  query.join('user_info', 'user_info.user_id = user.id')
        """
        info = {'table': table, 'on': on, 'type_': type_}
        self.__join.append(info)
        return self


    """
    数据缓存
    """
    __column_cache__ = {}

    def __get_cache(self, ck, default_value=None):
        item = self.__column_cache__.get(ck, default_value)
        if item is None:
            return None
        elif item['end_time'] <= int(time.time()):
            return None
        return item['data']

    def __set_cache(self, ck, value, timeout=60):
        item = {
            'end_time': int(time.time()) + timeout,
            'data': value,
        }
        self.__column_cache__[ck] = item
        return item['data']
