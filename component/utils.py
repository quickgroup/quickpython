import sys, traceback, json, time, threading, os, base64, mimetypes, logging, re
import hashlib, random, importlib, math
import datetime, copy
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import urlencode, urlparse
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)


class Utils():

    @staticmethod
    def empty(obj):
        if obj is None:     # 对象=none
            return True
        elif hasattr(obj, '__len__') and len(obj) == 0:
            return True
        elif isinstance(obj, str) and len(obj) == 0:
            return True
        elif isinstance(obj, dict) and len(obj) == 0:
            return True
        elif isinstance(obj, list) and len(obj) == 0:
            return True
        return False

    @staticmethod
    def not_empty(obj):
        return Utils.empty(obj) is False

    # 字符串json转字典
    @staticmethod
    def json_parse(strs, to_obj=False):
        try:
            if strs == None or len(strs) == 0:
                return None
            strs = str(strs, encoding='utf-8') if isinstance(strs, bytes) else strs
            data = json.loads(strs, encoding='utf8')
            if to_obj:  # 转为对象进行操作
                class Dict(dict):
                    __setattr__ = dict.__setitem__
                    __getattr__ = dict.__getitem__
                return Dict(data)
            return data
        except:
            logging.error("JSON 数据解析失败, strs=" + str(strs))
            Utils.print_exc()
        return None

    # 字典转json字符串
    @staticmethod
    def json_stringify(dicts):
        # 对含有日期格式数据的json数据进行转换
        from datetime import datetime
        from datetime import date
        from decimal import Decimal
        class JsonCustomEncoder(json.JSONEncoder):
            def default(self, field):
                if isinstance(field, datetime):
                    return field.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(field, date):
                    return field.strftime('%Y-%m-%d')
                elif isinstance(field, Decimal):
                    return field.to_eng_string()
                elif hasattr(field, '__dict__'):
                    return field.__dict__()
                else:
                    return json.JSONEncoder.default(self, field)

        try:
            if dicts is None:
                return None
            return json.dumps(dicts, cls=JsonCustomEncoder, ensure_ascii=False)
        except:
            print("字典转json字符串失败, dicts=", dicts)
            Utils.print_exc()
        return None

    @staticmethod
    def dict_to_str(dicts):
        """字典转json字符串"""
        try:
            import decimal
            class JsonEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, decimal.Decimal):
                        return float(obj)
                    if isinstance(obj, datetime.date):
                        return obj.strftime("%Y-%m-%d")
                    if isinstance(obj, datetime.time):
                        return obj.strftime("%H:%M:%S")
                    if isinstance(obj, datetime.datetime):
                        return obj.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(obj, '__dict__'):
                        return obj.__dict__()
                    return json.JSONEncoder.default(self, obj)

            json_dicts = json.dumps(dicts, indent=4, ensure_ascii=False, cls=JsonEncoder)
            return json_dicts
        except:
            print("字典打印失败, dicts=", dicts)
            Utils.print_exc()
        return None

    @staticmethod
    def print_dicts(dicts):
        """字典转json字符串打印"""
        print(Utils.dict_to_str(dicts))

    # 打印异常
    @staticmethod
    def print_exc():
        exc_type, exc_value, exc_tb = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_tb)

    @staticmethod
    def print_df(df, name='df'):
        df_len = 0 if df is None else len(df)
        logger.debug("{} {}\n{}".format(name, df_len, df))

    # 字典转json字符串
    @staticmethod
    def dict2format_str(dicts):
        try:
            json_dicts = json.dumps(dicts, indent=4, ensure_ascii=False)
            return json_dicts
        except:
            logging.error("字典打印失败, dicts={}".format(dicts))
            Utils.print_exc()
        return None

    @staticmethod
    def list_random_sort(arr):
        random.shuffle(arr)
        return arr

    # 异常转字符串
    @staticmethod
    def exc_string():
        error = traceback.format_exc()
        # error = str(error).replace(r"\n", "\n")   # traceback.format_exc() 不需要处理了
        # error = error.replace("\\\\",  "\\")
        return error

    @classmethod
    def time(cls):
        return cls.stime()

    @classmethod
    def stime(cls):
        return int(time.time())

    @staticmethod
    def mtime():
        return int(time.time() * 1000)

    @staticmethod
    def print_mtime():
        mtime = Utils.mtime()
        print('mtime', mtime)
        return mtime

    # 秒时间戳转日期时间
    @staticmethod
    def time_to_datetime(num=None, foramt="%Y-%m-%d %H:%M:%S", to_dt=False):
        dt = time.strftime(foramt, time.localtime(num))
        return Utils.parse_datetime(dt) if to_dt else dt

    # 毫秒时间戳转日期时间
    @staticmethod
    def mtime_to_date(num):
        return Utils.time_to_datetime(num / 1000)

    # 休眠
    @staticmethod
    def sleep(num, msg=None, every_print=False, for_show=True):
        if num < 1 or for_show is False:
            time.sleep(num)
            return True
        for fi in range(num):
            if fi == 0:
                logging.info("{}{}s后继续".format("" if msg is None else msg + " ", num))
            if every_print:
                logging.info("{}{}s后继续".format("" if msg is None else msg + " ", num-fi))
            time.sleep(1)

    # 读取文件内容
    @staticmethod
    def file_read(path, is_str=True):
        # 判断文件存在
        if os.path.exists(path) is False:
            raise Exception("文件不存在：" + path)
        # 读取文件内容
        file = open(path, 'rb')
        content = file.read()
        file.close()
        return content if is_str is False else str(content, encoding='utf8')

    # 写入文件内容
    @staticmethod
    def file_write(path, content):
        if isinstance(content, str):
            content = content.encode()
        # 上级目录存在
        path_dir = os.path.dirname(path)
        if len(path_dir) > 0 and os.path.exists(path_dir) is False:
            os.makedirs(path_dir)
        # 写入文件内容
        file = open(path, 'wb')
        file.write(content)
        file.close()
        return True

    @staticmethod
    def base64_encode(data):
        if isinstance(data, str) == True:
            data = data.encode("utf-8")
        return str(base64.b64encode(data), encoding='utf8')

    # base64加密
    @staticmethod
    def base64_decode(data, to_str=True):
        result = base64.b64decode(data)
        return str(result, encoding='utf8') if to_str else result

    # base64加密
    @staticmethod
    def base64_encode_file(file_path):
        with open(file_path, "rb") as f:
            content = f.read()
            return base64.b64encode(content)

    @staticmethod
    def rsa_encrypt(message, public_key, ret_encode=False):
        """校验RSA加密 使用公钥进行加密"""
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        cipher = PKCS1_v1_5.new(RSA.importKey(public_key))
        ret = cipher.encrypt(message.encode())
        return base64.b64encode(ret).decode() if ret_encode else ret

    @staticmethod
    def rsa_decrypt(data, private_key, data_decode=False):
        """校验RSA加密 使用私钥进行解密"""
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        cipher = PKCS1_v1_5.new(RSA.importKey(private_key))
        if data_decode:
            data = base64.b64decode(data)
        retval = cipher.decrypt(base64.b64decode(data), 'ERROR').decode('utf-8')
        return retval

    # url编码, 字典转url
    @staticmethod
    def url_encode(dicts):
        return urlencode(dicts)

    # url解析
    @staticmethod
    def url_decode(strs):
        return urlparse(strs)

    @staticmethod
    def html_escape(text):
        """html 符号转义：<p>转成&lt;p&gt;"""
        import html
        return html.escape(text)

    @staticmethod
    def html_unescape(text):
        """html 符号转义：&lt;p&gt;转成<p>"""
        import html
        return html.unescape(text)

    # 随机数
    @staticmethod
    def rand_int(start=0, end=999):
        # 结果包含end， start <= result <= end
        return random.randint(start, end)

    # 随机字符串
    @staticmethod
    def rand_str(length=1):
        return ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba0123456789', length))

    # 随机数
    @staticmethod
    def rand_number_arr(start=0, end=999, count=1, count_max=1):
        count = random.randint(count, count_max)
        return random.sample(range(start, end), count)

    # 数组搜索
    @staticmethod
    def array_in(arr, val):
        for idx in arr:
            if idx == val:
                return True
        return False

    # 数组或字典一维字符串转数字
    @staticmethod
    def array_value_2_int(arr):
        for idx in arr:
            if isinstance(arr[idx], str):
                arr[idx] = re.compile('\d+').findall(arr[idx])[0]
            arr[idx] = int(arr[idx])
        return arr

    # 获取字符串md5
    @staticmethod
    def md5_string(text):
        m = hashlib.md5()
        m.update(str(text).encode())
        return m.hexdigest()

    # 获取url信息
    @staticmethod
    def url_parse(url):
        info = urlparse(url)
        return info.scheme, info.netloc, info.path

    # 文件存在
    @staticmethod
    def file_exist(file_path):
        return os.path.exists(file_path)

    # 文件存在
    @staticmethod
    def file_del(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    # 获取文件mime
    @staticmethod
    def file_mime(file_path):
        return mimetypes.guess_type(file_path)[0]
    
    # 输入y继续，否则卡住
    @staticmethod
    def wait_key_continue():
        print('输入y进入下一步')
        while input() != 'y': print('输入y进入下一步')

    @staticmethod
    def mkdirs(paths):
        if os.path.exists(paths) is False:
            os.makedirs(paths)
            return True # 创建成功
        return False

    @staticmethod
    def datetime_to_timestamp(text:str, format_="%Y-%m-%d %H:%M:%S"):
        if text is None:
            return None
        struct_time = time.strptime(str(text), format_)  # 定义格式
        return int(time.mktime(struct_time))

    @staticmethod
    def parse_datetime(text):
        if text is None:
            return None
        if isinstance(text, datetime.datetime):
            return text
        from dateutil import parser as dt_parser
        return dt_parser.parse(str(text))

    @staticmethod
    def parse_date(val):
        import pandas
        if val is None:
            return None
        if isinstance(val, pandas._libs.tslibs.timestamps.Timestamp):
            val = val.date()
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
        from dateutil import parser as dt_parser
        return dt_parser.parse(str(val)).date()

    @staticmethod
    def new_datetime(*args, **kwargs):
        return datetime.datetime(*args, **kwargs)

    @staticmethod
    def datetime_now(extend_mtime=False):
        if extend_mtime:
            return datetime.datetime.now()
        return Utils.parse_datetime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def datetime_day_start_end(curr_dt):
        start_time = Utils.parse_datetime('{} 0:0:0'.format(curr_dt.date()))
        end_time = Utils.parse_datetime('{} 23:59:59'.format(curr_dt.date()))
        return start_time, end_time

    @staticmethod
    def datetime_yesterday_end(curr_dt=None):
        if curr_dt is None:
            curr_dt = Utils.datetime_now()
        yesterday_dt = Utils.datetime_add(curr_dt, -1)
        yesterday_dt = yesterday_dt.strftime("%Y-%m-%d 23:59:59")
        return Utils.parse_datetime(yesterday_dt)

    @staticmethod
    def datetime_add(dt, days=0, seconds=0, microseconds=0,
                milliseconds=0, minutes=0, hours=0, weeks=0):
        """负数是减"""
        if isinstance(dt, datetime.datetime) is False:
            dt = Utils.parse_datetime(str(dt))
        return dt + datetime.timedelta(days=days, seconds=seconds, microseconds=microseconds,
                milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)

    @staticmethod
    def date_to_int(dt):
        dt = Utils.parse_datetime(dt)
        return int(dt.strftime('%Y%m%d'))

    @staticmethod
    def time_conv_int(ti):
        return int(Utils.parse_datetime(ti).timestamp())

    @staticmethod
    def datetime_to_int(dt):
        dt = Utils.parse_datetime(dt)
        return int(dt.strftime('%Y%m%d%H%M%S'))

    @staticmethod
    def generate_date_list(start, end):
        import pandas
        return [x.strftime('%Y-%m-%d') for x in list(pandas.date_range(start=start, end=end))]

    __TIME_CACHE = {}

    @staticmethod
    def generate_time_list(start='00:00:00', end='23:59:59', to_time=False):
        import pandas
        ret = list(pandas.date_range(start=str(start), end=str(end), freq='s'))
        return [x.time() for x in ret] if to_time else [x.strftime('%H:%M:%S') for x in ret]

    @staticmethod
    def dict_filter(target, fileds):
        res = {}
        filed_arr = fileds.split(',')
        for it in filed_arr:
            it = str(it).strip()
            if len(it) == 0:
                continue
            res[it] = target[it] if it in target else None
        del filed_arr
        return res

    # 提取字符串中的数字
    @staticmethod
    def str_parse_float(text):
        return re.compile(r"\d+\.?\d*").findall(text)

    @staticmethod
    def str_to_hump(text, first_upper=True):
        ret = re.sub(r'(_[a-z])', lambda x: x.group(1)[1].upper(), text)
        if first_upper:
            ret = ret[0].upper() + ret[1:]
        return ret

    # 提取字符串中的数字
    @staticmethod
    def parse_int(text):
        try:
            return int(re.findall("\d+", str(text))[0])
        except BaseException as ex:
            logging.error("解析数字异常：\ntext={}\n{}".format(text, Utils.exc_string()))
            raise ex

    # 提取字符串中的数字
    @staticmethod
    def parse_int_arr(text):
        try:
            ret = re.findall("\d+", str(text))
            return [int(it) for it in ret]
        except BaseException as ex:
            logging.error("解析数字异常：\ntext={}\n{}".format(text, Utils.exc_string()))
            raise ex

    @staticmethod
    def threading(method, args):
        return threading.Thread(target=method, args=args)

    @staticmethod
    def timeout(method, args, sleep=0):
        def wait_func():
            time.sleep(sleep)
            method(args)
        thr = threading.Thread(target=wait_func)
        thr.start()
        return thr
        # thr.join()

    @staticmethod
    def thread_pool(func, data_list, max_workers=5):
        if len(data_list) == 0:
            return []
        pool_executor = ThreadPoolExecutor(max_workers=max_workers)
        if isinstance(data_list[0], tuple):
            thr_list = [pool_executor.submit(func, *data_list[idx]) for idx in range(len(data_list))]
        else:
            thr_list = [pool_executor.submit(func, data_list[idx]) for idx in range(len(data_list))]
        pool_executor.shutdown()
        result_list = [thr.result() for thr in thr_list]
        return result_list

    @staticmethod
    def process_pool(func, data_list, max_workers=5):
        pool_executor = ProcessPoolExecutor(max_workers=max_workers)
        thr_list = [pool_executor.submit(func, data_list[idx]) for idx in range(len(data_list))]
        pool_executor.shutdown()
        result_list = [thr.result() for thr in thr_list]
        return result_list

    @staticmethod
    def code_norm(code):
        # 前面带点的
        if code[:3] == 'sh.':
            code = code.replace('sh.', '') + ".SH"
        elif code[:3] == 'sz.':
            code = code.replace('sz.', '') + ".SZ"
        # 不带点的
        elif code[:2] == 'sh':
            code = code.replace('sh', '') + ".SH"
        elif code[:2] == 'sz':
            code = code.replace('sz', '') + ".SZ"
        return code

    @staticmethod
    def code_norm_to_prefix_lower(code, point='.'):
        if code[-3:] == '.SH':
            code = "sh" + point + code.replace('.SH', '')
        elif code[-3:] == '.SZ':
            code = 'sz' + point + code.replace('.SZ', '')
        return code

    @staticmethod
    def code_norm_to_prefix_upper(code, point='.'):
        if code[-3:] == '.SH':
            code = "SH" + point + code.replace('.SH', '')
        elif code[-3:] == '.SZ':
            code = 'SZ' + point + code.replace('.SZ', '')
        return code

    @staticmethod
    def os_proc_list():
        import psutil
        prcos = []
        for proc in psutil.process_iter():
            try:
                info = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
                if info['cmdline'] is not None and len(info['cmdline']) < 20:  # 过滤掉参数过多的进程
                    prcos.append(info)
            except psutil.NoSuchProcess:
                pass
        return prcos

    @staticmethod
    def os_kill_proc(pid, name=None):
        import psutil
        try:
            proc = psutil.Process(pid)
            if proc is not None:
                logger.info('find and kill {} PID={}'.format(proc.name(), pid))
                proc.kill()
                proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired) as e:
            logger.info('process PID={} not found'.format(pid))

        return True

    @staticmethod
    def dict_add_to(data, name, val=None):
        data[name] = data[name] if name in data else val
        return data

    @staticmethod
    def df_filter(df, columns):
        import pandas as pd
        return df[columns] if len(df) > 0 else pd.DataFrame([], columns=columns)

    @classmethod
    def math(cls):
        return math

    @staticmethod
    def copy():
        return copy


class ExtendUtils:
    """扩展库方法：非常用方法"""

    @classmethod
    def address_parse(cls, address):
        addr = str(address)
        prov = ''
        city = ''
        area = ''
        street = ''

        ret = re.findall(r'(.*?(省|自治区))', addr)
        if len(ret) > 0:
            prov = ret[0][0]
            addr = addr.replace(prov, '')
        ret = re.findall(r'(.*?(市|自治州|地区|区划|县))', addr)
        if len(ret) > 0:
            city = ret[0][0]
            addr = addr.replace(city, '')
        ret = re.findall(r'(.*?(区|县|镇|乡|街道))', addr)
        if len(ret) > 0:
            area = ret[0][0]
            addr = addr.replace(area, '')
            street = address[address.find(area) + len(area):]

        zxs_city = ['北京市', '天津市', '重庆市', '上海市']
        if city in zxs_city:
            prov = city

        return {'province': prov, 'city': city, 'area': area, 'street': street}


class Debug:
    """Debug工具"""

    __local = threading.local()

    @staticmethod
    def tag(tag):
        info = {'start_time': Utils.mtime()}
        Debug.__local.__setattr__('_debug_tag_' + tag, info)

    @staticmethod
    def tag_end(tag, name=None):
        name = tag if name is None else name
        info = Debug.__local.__getattribute__('_debug_tag_' + tag)
        logger.debug("TAG-{}耗时{}ms".format(name, Utils.mtime() - info['start_time']))


class DictObject:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, item):
        return None

    def __str__(self):
        return "DictObject=" + str(self.__dict__)

    @classmethod
    def parse(cls, data):
        d = DictObject.__new__(DictObject)
        d.__dict__.update(data)
        return d


import inspect


class ClassUtils:

    STATIC_METHODS = {}     # 静态方法
    INS_CLASS = {}          # 单例类

    @staticmethod
    def load_static_method(path):
        """加载静态方法"""
        if path in ClassUtils.STATIC_METHODS:
            return ClassUtils.STATIC_METHODS[path]
        # 创建
        clazz_info = str(path).split("#")
        model_path, clazz_name = clazz_info[0].rsplit(".", 1)
        module = importlib.import_module(model_path)
        clazz = getattr(module, clazz_name)
        method = getattr(clazz, clazz_info[1])
        ClassUtils.STATIC_METHODS[path] = method     # 缓存
        return method

    @staticmethod
    def load_object_dz(path, **kwargs):
        """字符串加载类方法（每次都创建对象"""
        clazz_info = str(path).split("#")
        model_path, clazz_name = clazz_info[0].rsplit(".", 1)
        module = importlib.import_module(model_path)
        obj = getattr(module, clazz_name)(**kwargs)
        return obj

    @staticmethod
    def load_method(path, **kwargs):
        """字符串加载类方法（每次都创建对象"""
        is_ins = kwargs.pop('is_ins', True)
        info = str(path).split("#")
        if is_ins and info[0] in ClassUtils.INS_CLASS:
            obj = ClassUtils.INS_CLASS.get(info[0])
        else:
            model_path, clazz_name = info[0].rsplit(".", 1)
            module = importlib.import_module(model_path)
            obj = getattr(module, clazz_name)(**kwargs)

        method = getattr(obj, info[1])
        return method

    @staticmethod
    def load_object(path):
        """Load an object given its absolute object path, and return it.
        object can be a class, function, variable or an instance.
        path ie: 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware'
        """
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ValueError("Error loading object '%s': not a full path" % path)
        module, name = path[:dot], path[dot + 1:]
        mod = importlib.import_module(module)
        try:
            obj = getattr(mod, name)
        except AttributeError:
            raise NameError("Module '%s' doesn't define any object named '%s'" % (module, name))
        return obj

    @staticmethod
    def get_current_function_name(idx=3):
        return inspect.stack()[1][idx]


class BaseClass:

    _logger_level = logging.DEBUG

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self._logger_level)
        self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):
        pass

    @classmethod
    def instance(cls, *args, **kwargs):
        clazz = cls
        if hasattr(clazz, '__instance_lock__') is False:
            clazz.__instance_lock__ = threading.Lock()
        if hasattr(clazz, '_instance') is False:
            with clazz.__instance_lock__:
                if hasattr(clazz, '_instance') is False:
                    clazz._instance = clazz(*args, **kwargs)
        return clazz._instance

    def call(self, argv):
        """支持cmd模式方法调用"""
        if hasattr(self, argv[0]) is False:
            raise Exception("方法不存在：{}".format(argv[0]))
        getattr(self, argv[0])()


class TestsClass(BaseClass):

    def call(self, argv):
        self.logger.info("{} 测试开始".format(argv[0]))
        super().call(argv)
        self.logger.info("{} 测试完成".format(argv[0]))


class Calc:

    DIGITS = 3

    @staticmethod
    def Decimal(val):
        return Decimal(str(val))

    @staticmethod
    def digits(val, digits=None):
        if isinstance(val, Decimal) is False:
            val = Decimal(str(val))
        if digits is None:
            digits = Calc.DIGITS
            # return result
        digits_str = "".join([str(it) for it in range(digits)])
        digits_val = Decimal('0.' + digits_str)
        return val.quantize(digits_val, rounding=ROUND_DOWN)

    @staticmethod
    def __common(opt, val, val2, digits=None):
        try:
            if val is None or val2 is None:
                raise Exception("错误的操作数据 val={}, val2={}".format(val, val2))
            elif opt == 'add':
                result = Decimal(str(val)) + Decimal(str(val2))
            elif opt == 'sub':
                result = Decimal(str(val)) - Decimal(str(val2))
            elif opt == 'mul':
                result = Decimal(str(val)) * Decimal(str(val2))
            elif opt == 'div':
                result = Decimal(str(val)) / Decimal(str(val2))
            else:
                result = None
            return Calc.digits(result, digits)

        except BaseException as e:
            logger.exception('opt={}, val={}, val2={}, digits={}'.format(opt, val, val2, digits))
            raise e

    @staticmethod
    def add(val, val2, digits=None):
        return Calc.__common('add', val, val2, digits)

    @staticmethod
    def sub(val, val2, digits=None):
        return Calc.__common('sub', val, val2, digits)

    @staticmethod
    def mul(val, val2, digits=None):   # 乘
        return Calc.__common('mul', val, val2, digits)

    @staticmethod
    def div(val, val2, digits=None):   # 除
        return Calc.__common('div', val, val2, digits)

    @staticmethod
    def abs(val, digits=None):      # 绝对值
        return Calc.digits(Decimal(str(math.fabs(val))), digits)

    @staticmethod
    def ceil(val, digits=None):     # 向上取整
        return Calc.digits(Decimal(str(math.ceil(val))), digits)

    @staticmethod
    def floor(val, digits=None):     # 向下取整
        return Calc.digits(Decimal(str(math.floor(val))), digits)

