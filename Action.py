
import os
import sys
import imp
from RandomFileQueue import RandomFileQueue
from weakref import WeakKeyDictionary
from threading import RLock
import Downloader
import TaskSystem
import Index

# First some code with some module reload handling logic to make hacking on it more fun.

def _reloadHandler():
	import RandomFileQueue
	import Index
	import FileSysIntf
	import Downloader
	for mod in [RandomFileQueue, Index, FileSysIntf, Downloader]:
		try:
			imp.reload(mod)
		except Exception:
			sys.excepthook(*sys.exc_info())

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

def pushRandomNextFile():
	base = Index.index.getRandomSource()
	walker = getRandomWalker(base)
	url = walker.getNextFile()
	if not url: return
	def download():
		Downloader.download(url)
	TaskSystem.queueWork(download)

def getNewAction():
	if _checkMaybeReload():
		import Action
		return Action.getNewAction()

	return pushRandomNextFile

