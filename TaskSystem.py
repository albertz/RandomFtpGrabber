
from queue import Queue
from threading import currentThread, Event, RLock, Lock, Thread
import weakref
import sys

kNumWorkers = 5
kMinQueuedActions = kNumWorkers # fill workerQueue always up to N elements, via the watcher thread

mainThread = currentThread() # expect that we import this from the main thread
mainLoopQueue = Queue()
workerQueue = Queue()
exitEvent = Event()


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


def queueWork(func):
	workerQueue.put(func)


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

def workerLoop():
	while True:
		func = workerQueue.get()
		try:
			func()
		except KeyboardInterrupt:
			return

def watcherLoop():
	while not exitEvent.isSet():
		if workerQueue.qsize() >= kMinQueuedActions:
			exitEvent.wait(1)
			continue

		import Action
		func = Action.getNewAction()
		workerQueue.put(func)

workers = []
watcher = None

def _initWorkerThreads():
	for i in range(kNumWorkers):
		thread = Thread(target=workerLoop, name="Worker %i/%i" % (i + 1, kNumWorkers))
		workers.append(thread)
		thread.daemon = True
		thread.start()

def _initWatcherThread():
	global watcher
	watcher = Thread(target=watcherLoop, name="Watcher")
	watcher.daemon = True
	watcher.start()

_initWatcherThread()
_initWorkerThreads()

