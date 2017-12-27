
import weakref
import pickle
import os
import sys
from PyReprHelpers import better_repr


# Use this class so that we can add methods to it (such as save()).
class Set(set):
    pass


class Saver:
    def __init__(self, obj, filename):
        self.obj = weakref.ref(obj)
        self.filename = filename

    def __call__(self):
        obj = self.obj()
        if obj:
            obj_repr = better_repr(obj)
            if obj_repr[0] == "<":
                raise Exception("non-repr-able object: %s" % obj_repr)
            f = open(self.filename, "w")
            f.write(obj_repr)
            f.close()


def load(filename, default_constructor, env=None):
    from PickleHelpers import is_pickle_format
    from PyReprHelpers import is_python_repr_format, load_python_repr_format
    import PickleHelpers
    PickleHelpers.setup()

    import main
    from Threading import DoInMainThreadDecoratorNowait
    import Logging

    filename = main.RootDir + "/" + filename
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            Logging.log("Persistence.load %s" % filename)
            if is_python_repr_format(filename):
                try:
                    obj = load_python_repr_format(filename, defaultConstructor=default_constructor, env=env)
                except Exception:
                    sys.excepthook(*sys.exc_info())
                    sys.exit(1)
            elif is_pickle_format(filename):
                obj = pickle.load(open(filename, "rb"))
            else:
                raise Exception("unknown format in %s" % filename)
        except Exception:
            Logging.log_exception("Persistence.load %s" % filename, *sys.exc_info())
            obj = default_constructor()
    else:
        obj = default_constructor()

    if isinstance(obj, set) and not isinstance(obj, Set):
        obj = Set(obj)

    # Set obj.save() function.
    saver = Saver(obj, filename)
    obj.save = DoInMainThreadDecoratorNowait(saver)
    saver()  # save now

    return obj

