
import Persistence
import FileSysIntf
from TaskSystem import SyncedOnObj
import random
import Logging

# Interface for RandomFileQueue
class Filesystem:
	def listDir(self, path):
		return path.listDir()

	def isFile(self, path):
		return isinstance(path, File)

	def isDir(self, path):
		return isinstance(path, Dir)

	def handleException(self, exctype, value, traceback):
		Logging.logException("Filesystem", exctype, value, traceback)

class FileBase:
	def __init__(self, url):
		self.url = url

	def __str__(self):
		return self.url

class File(FileBase): pass

class Dir(FileBase):
	def __init__(self, url):
		super().__init__(url)
		self.childs = None
		self.lastException = None

	@SyncedOnObj
	def listDir(self):
		if self.childs is not None:
			return self.childs

		try:
			dirs, files = FileSysIntf.listDir(self.url)
		except Exception as e:
			print(e)

			self.lastException = e
			return []

		self.childs = \
			list(map(Dir, dirs)) + \
			list(map(File, files))
		index.save()
		return self.childs

	def __str__(self):
		return self.url

class Index:
	def __init__(self):
		self.sources = {}
		self._loadSources()
		assert self.sources

	def _loadSources(self):
		import main
		for source in main.Sources:
			self.sources[source] = Dir(url=source)

	def getRandomSource(self):
		return random.choice(list(self.sources.values()))

filesystem = Filesystem()

index = Persistence.load("index.db", Index)
