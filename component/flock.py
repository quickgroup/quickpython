import sys


IS_WIN32 = sys.platform == "win32"
if IS_WIN32 is False:
    import fcntl


class FLock:
    LOCK_EX: int
    LOCK_NB: int
    LOCK_SH: int
    LOCK_UN: int

    def __init__(self, file_name):
        self.file_name = file_name
        self.fd = None

    def fcntl(self, op, arg=0):
        pass

    def ioctl(self, op, arg=0, mutable_flag=True):
        if mutable_flag:
            return 0
        else:
            return ""

    def flock(self, op):
        if IS_WIN32:
            pass
        else:
            self.fd = open(self.file_name, 'w+')
            fcntl.fcntl(self.fd, fcntl.LOCK_EX)

    def lockf(self, operation, length=0, start=0, whence=0):
        pass

    def lock(self, op):
        return self.flock(fcntl.LOCK_EX)

    def unlock(self, op):
        return self.flock(fcntl.LOCK_UN)
