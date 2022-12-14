"""
    ORM框架配置
"""
from quickpython.component.env import env


# 数据库连接配置
DATABASES = {
    'default': {
        'engine': 'mysql',
        'hostname': env.get('database.hostname', "127.0.0.1"),
        'database': env.get('database.database', "root"),
        'username': env.get('database.username', "root"),
        'password': env.get('database.password', "root"),
        'port': env.get('database.port', 3306),
        'prefix': env.get('database.prefix', ""),
        'echo': env.get('database.echo', True),
        'echo_words': env.get('database.echo_words', 256),
        'wait_timeout': env.get('database.wait_timeout', 3600),
        'bulk_size': env.get('database.bulk_size', 500),  # 每次批量新增更新每次最大数量
        'options': {
            'init_command': 'SET default_storage_engine=INNODB;',
            'charset': 'utf8',
            'table_prefix': "",  # 表名前缀，todo::暂不支持
            'field_sep': True,      # 开启字段表名分割符，例：`id` or id
            'val_str_sep': "\"",    # 字符数据包围符号 只能是'和"
            'with_seq': "__",       # 预载入表字段关联前缀
            'datetime_fmt': "",     # 时间格式
        },
    },
}

