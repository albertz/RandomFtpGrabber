
from RandomFileQueue import RandomFileQueue
from weakref import WeakKeyDictionary
from threading import RLock
import Downloader
import TaskSystem
import Index
import FileSysIntf


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
		if not isinstance(other, Download): return False
		return str(self.url) == str(other.url)

	def __lt__(self, other):
		if not isinstance(other, Download): return False
		return str(self.url) < str(other.url)

	def __repr__(self):
		return "Download(%r)" % str(self.url)


class RandomNextFile:
	def __init__(self):
		self.base = Index.index.getRandomSource()

	def __call__(self):
		walker = getRandomWalker(self.base)
		try:
			url = walker.getNextFile()
		except FileSysIntf.TemporaryException:
			# Handled in walker.
			# We just quit here now.
			return
		if not url: return
		TaskSystem.queueWork(Download(url))

	def __hash__(self):
		return hash(self.base)

	def __eq__(self, other):
		if not isinstance(other, RandomNextFile): return False
		return str(self.base.url) == str(other.base.url)

	def __lt__(self, other):
		if isinstance(other, Download): return True
		if not isinstance(other, RandomNextFile): return False
		return str(self.base.url) < str(other.base.url)

	def __repr__(self):
		# Doesn't matter which base, just take another random next time.
		return "RandomNextFile()"


def getNewAction():
	return RandomNextFile()

