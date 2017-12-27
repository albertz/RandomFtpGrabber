
import sys
import weakref
from threading import current_thread, Event, RLock, Lock


mainThread = current_thread()  # expect that we import this from the main thread


def do_in_main_thread(func, wait):
    import TaskSystem

    if not wait:  # don't wait
        TaskSystem.mainLoopQueue.put(func)
        return

    if current_thread() is mainThread:
        return func()
    else:
        class Result:
            doneEvent = Event()
            returnValue = None
            excInfo = None

        def wrapped():
            try:
                Result.returnValue = func()
            except BaseException:
                Result.excInfo = sys.exc_info()
            Result.doneEvent.set()

        TaskSystem.mainLoopQueue.put(wrapped)
        Result.doneEvent.wait()
        if Result.excInfo:
            raise Result.excInfo[1]
        return Result.returnValue


class Caller:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.func()


class DoInMainThreadDecoratorWait:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return do_in_main_thread(Caller(self.func, *args, **kwargs), wait=True)


class DoInMainThreadDecoratorNowait:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return do_in_main_thread(Caller(self.func, *args, **kwargs), wait=False)


class LocksDict:
    def __init__(self, lock_clazz=RLock):
        self.lockClazz = lock_clazz
        self.lock = Lock()
        self.weakKeyDict = weakref.WeakKeyDictionary()

    def __getitem__(self, item):
        with self.lock:
            if item in self.weakKeyDict:
                return self.weakKeyDict[item]
            lock = self.lockClazz()
            self.weakKeyDict[item] = lock
            return lock


def synced_on_obj(func):
    locks = LocksDict()

    def decorated_func(self, *args, **kwargs):
        with locks[self]:
            return func(self, *args, **kwargs)

    return decorated_func
