"""
    python-quick.env 1.0
    环境变量管理器
"""
import os, logging


class Env:

    def __init__(self, env_path=".env", encoding="utf-8"):
        self.env_path = env_path
        self.encoding = encoding
        self._DATA = {}
        self.load_env(env_path)

    def load_env(self, env_path):
        """加载本地.env文件"""
        if os.path.exists(env_path) is False:
            raise "env file '{}' not found".format(env_path)
            # return logging.warning("env file '{}' not found".format(env_path))

        self.encoding = "utf-8" if self.encoding is None else self.encoding

        with open(env_path, encoding=self.encoding) as fp:
            lines = fp.readlines()
            group_name = None
            for line in lines:
                if line[-1] == "\n":
                    line = line[:-1]
                if line == '' or line[0] == '#':
                    continue
                # 组名
                if line[0] == '[' and line[-1] == ']':
                    group_name = line[1:-1]
                    self._DATA[group_name] = {}
                    continue
                # 数据
                ei = line.find("=")
                if ei == -1:
                    continue

                key, val = line[:ei].strip(), line[ei+1:].strip()
                # 数据实例化
                if len(val) == 0: val = ''
                elif val.lower() == "true": val = True
                elif val.lower() == "false": val = False

                if group_name is not None:
                    self._DATA[group_name][key] = val
                    self._write_os_env(group_name + '.' + key, val)
                else:
                    self._DATA[key] = val
                    self._write_os_env(key, val)

    def _write_os_env(self, k, v):
        if isinstance(v, str):
            os.environ.setdefault(k, v)
        else:
            os.environ.setdefault(k, '')

    def get(self, key:str, def_val=None):
        if key.find(".") > -1:
            key1, key2 = tuple(key.split("."))
            if key1 not in self._DATA:
                return def_val
            group = self._DATA.get(key1)
            return group.get(key2) if key2 in group else def_val
        else:
            return self._DATA.get(key) if key in self._DATA else def_val

    def set(self, key, val):
        if key.find(".") > -1:
            key1, key2 = tuple(key.split("."))
            if key1 not in self._DATA:
                self._DATA[key1] = {}
            self._DATA[key1][key2] = val
        else:
            self._DATA[key] = val

        return val

    @classmethod
    def __get_global__(cls):
        env = globals().get("__quickpython.component.env")
        if env is None:
            env = Env()
            globals()["__quickpython.component.env"] = env

        return env


env = Env.__get_global__()


if __name__ == "__main__":
    print("env", env)
    print("env", env.get("app"))
    print("env", env.get("app.debug"))
    print("env", env.get("database"))
    # 设置
    print("set", env.set("app.asd", "asd"))
    print("set", env.set("app.asd", True))
    print("set", env.get("app"))

