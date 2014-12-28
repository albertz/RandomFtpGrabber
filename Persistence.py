
from weakref import ref
import pickle
import os
import sys

class Saver:
	def __init__(self, obj, filename):
		self.obj = ref(obj)
		self.filename = filename

	def __call__(self):
		pickle.dump(self.obj, open(self.filename, "wb"))

def load(filename, defaultConstructor):
	import main
	from TaskSystem import DoInMainthreadDecoratorNowait
	import Logging

	filename = main.RootDir + "/index.db"
	if os.path.exists(filename):
		try:
			obj = pickle.load(open(filename, "rb"))
		except Exception:
			Logging.logException("Persistence.load", *sys.exc_info())
			obj = defaultConstructor()
	else:
		obj = defaultConstructor()

	# Set obj.save() function.
	obj.save = DoInMainthreadDecoratorNowait(Saver(obj, filename))

	return obj


def _pickle_method(method):
	func_name = method.im_func.__name__
	obj = method.im_self
	cls = method.im_class
	return _unpickle_method, (func_name, obj, cls)

def _pickle_function(func, **kwargs):
	print(func.__name__, func.__qualname__)
	import sys
	sys.exit(1)
	func_name = func.__name__
	return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
	func = cls.__dict__[func_name]
	return func.__get__(obj, cls)

def _pickle_weakref(r):
	return _unpickle_weakref, (r(),)

def _unpickle_weakref(obj):
	return ref(obj)

import copyreg
import types
copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)
copyreg.pickle(types.FunctionType, _pickle_function, _unpickle_method)
copyreg.pickle(ref, _pickle_weakref, _unpickle_weakref)
