
from threading import RLock
import better_exchook

lock = RLock()


def log_exception(where, exctype, value, traceback):
    with lock:
        print("Exception at %s" % where)
        better_exchook.better_exchook(exctype, value, traceback, autodebugshell=False)


def log(*args):
    with lock:
        print(*args)
