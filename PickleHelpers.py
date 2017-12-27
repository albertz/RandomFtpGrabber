
import os
import weakref
import queue
import copyreg
import types
import pickle


def is_pickle_format(filename):
    # http://stackoverflow.com/questions/13939913/how-to-test-if-a-file-has-been-created-by-pickle
    f = open(filename, "rb")
    f.seek(-1, os.SEEK_END)
    last_byte = f.read(1)
    if last_byte == pickle.STOP:
        return True
    return False


def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)


def _unpickle_method(func_name, obj, cls):
    func = cls.__dict__[func_name]
    return func.__get__(obj, cls)


def _pickle_function(func, **kwargs):
    import Logging
    Logging.log("Error, not supported to pickle functions!")
    Logging.log(func.__name__, func.__qualname__)
    import better_exchook
    better_exchook.print_tb(None)
    raise Exception("no function pickling possible")


def _pickle_weakref(r):
    return _unpickle_weakref, (r(),)


def _unpickle_weakref(obj):
    return weakref.ref(obj)


# noinspection PyPep8Naming
def _pickle_Queue(q):
    with q.mutex:
        ls = list(q.queue)
    return _unpickle_Queue, (ls,)


# noinspection PyPep8Naming
def _unpickle_Queue(ls):
    q = queue.Queue()
    q.queue = q.queue.__class__(ls)
    return q


_did_setup = False


def setup():
    global _did_setup
    if _did_setup:
        return
    _did_setup = True

    copyreg.pickle(types.MethodType, _pickle_method, _unpickle_method)
    copyreg.pickle(types.FunctionType, _pickle_function, _unpickle_method)
    copyreg.pickle(weakref.ref, _pickle_weakref, _unpickle_weakref)
    copyreg.pickle(queue.Queue, _pickle_Queue, _unpickle_Queue)

    # Must register in that module because old pickled files expect it there.
    import Persistence
    Persistence._unpickle_Queue = _unpickle_Queue
    Persistence._unpickle_method = _unpickle_method
    Persistence._unpickle_weakref = _unpickle_weakref

