
import os
import sys
import imp
from RandomFileQueue import RandomFileQueue
from weakref import WeakKeyDictionary
from threading import RLock
import Downloader
import TaskSystem
import Index
import FileSysIntf

# First some code with some module reload handling logic to make hacking on it more fun.

def _reloadHandler():
	import Logging
	import RandomFileQueue
	import Index
	import FileSysIntf
	import Downloader
	for mod in [Logging, RandomFileQueue, Index, FileSysIntf, Downloader]:
		try:
			imp.reload(mod)
		except Exception:
			Logging.logException("reloadHandler", *sys.exc_info())

def _getModChangeTime():
	return os.path.getmtime(__file__)

if "_modChangeTime" in vars():
	_reloadHandler()
_modChangeTime = _getModChangeTime()

def _checkMaybeReload():
	global modChangeTime
	mtime = _getModChangeTime()
	if mtime > _modChangeTime:
		_reload()
		return True
	return False

def _reload():
	print("reload Action module")
	import Action
	imp.reload(Action)


# Now the main actions.

lock = RLock()
randomWalkers = WeakKeyDictionary() # Dir -> RandomFileQueue

def getRandomWalker(base):
	with lock:
		if base in randomWalkers:
			return randomWalkers[base]
		walker = RandomFileQueue(rootdir=base, filesystem=Index.filesystem)
		randomWalkers[base] = walker
		return walker

class Download:
	def __init__(self, url):
		self.url = str(url)

	def __call__(self):
		try:
			Downloader.download(self.url)
		except Downloader.DownloadTemporaryError:
			# Retry later.
			TaskSystem.queueWork(self)
		except Downloader.DownloadFatalError:
			# Cannot handle. Nothing we can do.
			pass

	def __hash__(self):
		return hash(str(self.url))

	def __eq__(self, other):
		return str(self.url) == str(other.url)

	def __str__(self):
		return "Download: %s" % str(self.url)

	def __repr__(self):
		return "Download(%r)" % str(self.url)


def pushRandomNextFile():
	base = Index.index.getRandomSource()
	walker = getRandomWalker(base)
	try:
		url = walker.getNextFile()
	except FileSysIntf.TemporaryException:
		# Handled in walker.
		# We just quit here now.
		return
	if not url: return
	TaskSystem.queueWork(Download(url))

def getNewAction():
	if _checkMaybeReload():
		import Action
		return Action.getNewAction()

	return pushRandomNextFile

