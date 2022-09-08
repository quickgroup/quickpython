import sys, logging


LOCK_EX = 1
LOCK_NB = 2
LOCK_SH = 3
LOCK_UN = 4


IS_WIN32 = sys.platform == "win32"
if IS_WIN32:
    # pip install pypiwin32
    try:
        import win32con, win32file, pywintypes
        LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
        LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    except:
        pass

else:
    from fcntl import LOCK_EX, LOCK_SH, LOCK_NB
    import fcntl


class FLock:
    LOCK_EX = LOCK_EX
    LOCK_NB = LOCK_NB
    LOCK_SH = LOCK_SH
    LOCK_UN = LOCK_UN

    def __init__(self, file_name):
        self.file_name = file_name
        self.fd = open(file_name, 'w')
        if IS_WIN32:
            self.__overlapped__ = pywintypes.OVERLAPPED()

    def lock(self, flags=LOCK_EX):
        if IS_WIN32:
            hfile = win32file._get_osfhandle(self.fd.fileno())
            win32file.LockFileEx(hfile, flags, 0, 0xffff0000, self.__overlapped__)
        else:
            fcntl.flock(self.fd.fileno(), flags)

        return self

    def unlock(self):
        if IS_WIN32:
            hfile = win32file._get_osfhandle(self.fd.fileno())
            win32file.UnlockFileEx(hfile, 0, 0xffff0000, self.__overlapped__)
        else:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)

        return self

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, value, traceback):
        self.unlock()


if __name__ == '__main__':
    import threading, time
    formatter_str = '%(asctime)s %(levelname)s [%(filename)s:%(funcName)s:%(lineno)d]\t%(message)s'
    logging.basicConfig(format=formatter_str, level=logging.DEBUG, handlers=[logging.StreamHandler()])
    logging.info("测试文件锁")

    with open('test.file', 'w+') as f:
        f.seek(0)
        f.write("")
        f.flush()


    def opt_file(num):
        ident = threading.current_thread().ident

        # 使用方式一
        # flock = FLock('lock.file').lock()
        # with open('test.file', 'r+') as f:
        #     f.seek(0)
        #     content = f.read()
        #     logging.info('content={}'.format(content))
        #     content += "{}, thr={}\n".format(num, ident)
        #     f.seek(0)
        #     f.write(content)
        #     f.flush()
        # flock.unlock()

        # 使用方式二
        with FLock():
            with open('test.file', 'r+') as f:
                f.seek(0)
                content = f.read()
                logging.info('content={}'.format(content))
                content += "{}, thr={}\n".format(num, ident)
                f.seek(0)
                f.write(content)
                f.flush()

    thr_list = [threading.Thread(target=opt_file, args=(it,)) for it in range(10)]
    [thr.start() for thr in thr_list]

    logging.info("测试文件锁 完成")
