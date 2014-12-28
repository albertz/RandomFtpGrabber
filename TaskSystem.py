
from queue import Queue
from threading import currentThread, Event, RLock, Lock
import weakref
import sys

mainThread = currentThread() # expect that we import this from the main thread
mainLoopQueue = Queue()


def doInMainthread(func, wait):
	if not wait: # don't wait
		mainLoopQueue.put(func)
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
		mainLoopQueue.put(wrapped)
		result.doneEvent.wait()
		if result.excInfo: raise result.excInfo[1]
		return result.returnValue

def DoInMainthreadDecoratorWait(func):
	def decoratedFunc(*args, **kwargs):
		return doInMainthread(lambda: func(*args, **kwargs), wait=True)
	return decoratedFunc

def DoInMainthreadDecoratorNowait(func):
	def decoratedFunc(*args, **kwargs):
		return doInMainthread(lambda: func(*args, **kwargs), wait=False)
	return decoratedFunc

class LocksDict:
	def __init__(self, lockClazz=RLock):
		self.lockClazz = lockClazz
		self.lock = Lock()
		self.weakKeyDict = weakref.WeakKeyDictionary()

	def __getitem__(self, item):
		with self.lock:
			return self.weakKeyDict.get(item, self.lockClazz)

def SyncedOnObj(func):
	locks = LocksDict()
	def decoratedFunc(self, *args, **kwargs):
		with locks[self]:
			return func(self, *args, **kwargs)
	return decoratedFunc


def mainLoop():
	while True:
		func = mainLoopQueue.get()
		func()
