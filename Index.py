
import Persistence
import FileSysIntf
from TaskSystem import SyncedOnObj

# Interface for RandomFileQueue
class Filesystem:
	def listDir(self, path):
		return path.listDir()

	def isFile(self, path):
		return isinstance(path, File)

	def isDir(self, path):
		return isinstance(path, Dir)

class File:
	def __init__(self, url):
		self.url = url

class Dir:
	def __init__(self, url):
		self.url = url
		self.childs = None

	@SyncedOnObj
	def listDir(self):
		if self.childs is not None:
			return self.childs

		dirs, files = FileSysIntf.listDir(self.url)
		self.childs = \
			list(map(Dir, dirs)) + \
			list(map(File, files))
		return self.childs

class Index:
	def __init__(self):
		self.sources = {}
		self._loadSources()

	def _loadSources(self):
		import main
		for source in main.Sources:
			self.sources[source] = Dir(url=source)


filesystem = Filesystem()

index = Persistence.load("index.db", Index)
