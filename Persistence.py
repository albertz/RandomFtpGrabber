
import weakref
import pickle
import os
import sys
from PyReprHelpers import betterRepr


# Use this class so that we can add methods to it (such as save()).
class Set(set): pass


class Saver:
	def __init__(self, obj, filename):
		self.obj = weakref.ref(obj)
		self.filename = filename

	def __call__(self):
		obj = self.obj()
		if obj:
			objRepr = betterRepr(obj)
			if objRepr[0] == "<":
				raise Exception("non-repr-able object: %s" % objRepr)
			f = open(self.filename, "w")
			f.write(objRepr)
			f.close()


def load(filename, defaultConstructor, env=None):
	from PickleHelpers import isPickleFormat
	from PyReprHelpers import isPythonReprFormat, loadPythonReprFormat
	import PickleHelpers
	PickleHelpers.setup()

	import main
	from Threading import DoInMainthreadDecoratorNowait
	import Logging

	filename = main.RootDir + "/" + filename
	if os.path.exists(filename) and os.path.getsize(filename) > 0:
		try:
			if isPythonReprFormat(filename):
				try:
					obj = loadPythonReprFormat(filename, defaultConstructor=defaultConstructor, env=env)
				except:
					sys.excepthook(*sys.exc_info())
					sys.exit(1)
			elif isPickleFormat(filename):
				obj = pickle.load(open(filename, "rb"))
			else:
				raise Exception("unknown format in %s" % filename)
		except Exception:
			Logging.logException("Persistence.load %s" % filename, *sys.exc_info())
			obj = defaultConstructor()
	else:
		obj = defaultConstructor()

	if isinstance(obj, set) and not isinstance(obj, Set):
		obj = Set(obj)

	# Set obj.save() function.
	saver = Saver(obj, filename)
	obj.save = DoInMainthreadDecoratorNowait(saver)
	saver() # save now

	return obj

