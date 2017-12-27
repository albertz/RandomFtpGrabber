
import sys
import weakref
from threading import currentThread, Event, RLock, Lock

mainThread = currentThread() # expect that we import this from the main thread

def doInMainthread(func, wait):
    import TaskSystem

    if not wait: # don't wait
        TaskSystem.mainLoopQueue.put(func)
        return

    if currentThread() is mainThread:
        return func()
    else:
        class result:
            doneEvent = Event()
            returnValue = None
            excInfo = None
        def wrapped():
            try:
                result.returnValue = func()
            except BaseException:
                result.excInfo = sys.exc_info()
            result.doneEvent.set()
        TaskSystem.mainLoopQueue.put(wrapped)
        result.doneEvent.wait()
        if result.excInfo: raise result.excInfo[1]
        return result.returnValue

class Caller:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.func()

class DoInMainthreadDecoratorWait:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return doInMainthread(Caller(self.func, *args, **kwargs), wait=True)

class DoInMainthreadDecoratorNowait:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return doInMainthread(Caller(self.func, *args, **kwargs), wait=False)



class LocksDict:
    def __init__(self, lockClazz=RLock):
        self.lockClazz = lockClazz
        self.lock = Lock()
        self.weakKeyDict = weakref.WeakKeyDictionary()

    def __getitem__(self, item):
        with self.lock:
            if item in self.weakKeyDict:
                return self.weakKeyDict[item]
            lock = self.lockClazz()
            self.weakKeyDict[item] = lock
            return lock

def SyncedOnObj(func):
    locks = LocksDict()
    def decoratedFunc(self, *args, **kwargs):
        with locks[self]:
            return func(self, *args, **kwargs)
    return decoratedFunc
