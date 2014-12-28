
import weakref
import pickle
import os
import sys
import queue

class Saver:
	def __init__(self, obj, filename):
		self.obj = weakref.ref(obj)
		self.filename = filename

	def __call__(self):
		f = open(self.filename, "wb")
		obj = self.obj()
		pickle.dump(obj, f)

class Set(set): pass

def load(filename, defaultConstructor):
	import main
	from Threading import DoInMainthreadDecoratorNowait
	import Logging

	if defaultConstructor is set: defaultConstructor = Set

	filename = main.RootDir + "/" + filename
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

def _unpickle_method(func_name, obj, cls):
	func = cls.__dict__[func_name]
	return func.__get__(obj, cls)

def _pickle_function(func, **kwargs):
	print("Error, not supported to pickle functions!")
	print(func.__name__, func.__qualname__)
	import sys
	sys.exit(1)

def _pickle_weakref(r):
	return _unpickle_weakref, (r(),)

def _unpickle_weakref(obj):
	return weakref.ref(obj)

def _pickle_Queue(q):
	with q.mutex:
		l = list(q.queue)
	return _unpickle_Queue, (l,)

def _unpickle_Queue(l):
	q = queue.Queue()
	q.queue = q.queue.__class__(l)
	return q

import copyreg
import types
copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)
copyreg.pickle(types.FunctionType, _pickle_function, _unpickle_method)
copyreg.pickle(weakref.ref, _pickle_weakref, _unpickle_weakref)
copyreg.pickle(queue.Queue, _pickle_Queue, _unpickle_Queue)