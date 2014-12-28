
from queue import Queue
from threading import currentThread, Event, RLock, Lock, Thread
import weakref
import sys
import better_exchook

kNumWorkers = 5
kMinQueuedActions = kNumWorkers # fill workerQueue always up to N elements, via the watcher thread

mainThread = currentThread() # expect that we import this from the main thread
if not "mainLoopQueue" in vars():
	mainLoopQueue = Queue()
if not "workerQueue" in vars():
	workerQueue = Queue()
if not "exitEvent" in vars():
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


def queueWork(func):
	workerQueue.put(func)


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


def mainLoop():
	while True:
		func = mainLoopQueue.get()
		func()

def workerLoop():
	better_exchook.install()
	while True:
		func = workerQueue.get()
		try:
			func()
		except KeyboardInterrupt:
			return

def watcherLoop():
	better_exchook.install()
	while not exitEvent.isSet():
		if workerQueue.qsize() >= kMinQueuedActions:
			exitEvent.wait(1)
			continue

		import Action
		func = Action.getNewAction()
		workerQueue.put(func)

if "workers" not in vars():
	workers = []
if "watcher" not in vars():
	watcher = None

def _initWorkerThreads():
	if len(workers) >= kNumWorkers: return
	for i in range(kNumWorkers - len(workers)):
		thread = Thread(target=workerLoop, name="Worker %i/%i" % (i + 1, kNumWorkers))
		workers.append(thread)
		thread.daemon = True
		thread.start()

def _initWatcherThread():
	global watcher
	if watcher: return
	watcher = Thread(target=watcherLoop, name="Watcher")
	watcher.daemon = True
	watcher.start()

_initWatcherThread()
_initWorkerThreads()

