
import re
import sys
from collections import deque
from queue import Queue


def isPythonReprFormat(filename):
    try:
        f = open(filename, "r")
        firstByte = f.read(1)
        # List, dict, tuple, string or number.
        if firstByte in "[{(\"'0123456789-":
            return True
        f.seek(0)
        beginning = f.read(100)
        # Maybe some identifier.
        if re.match("[_A-Za-z][_a-zA-Z0-9.]*\(.*", beginning):
            return True
    except UnicodeDecodeError:
        return False
    return False

def loadPythonReprFormat(filename, env=None, defaultConstructor=None):
    code = open(filename, "r").read()
    if not env:
        env = {}
    elif isinstance(env, list):
        env = dict([(o.__name__, o) for o in env])
    else:
        env = dict(env)
    env["loadQueue"] = loadQueue
    if hasattr(defaultConstructor, "__module__"):
        env.update(vars(sys.modules[defaultConstructor.__module__]))
    elif hasattr(defaultConstructor, "__name__"):
        env[defaultConstructor.__name__] = defaultConstructor
    return eval(code, env)


def loadQueue(l):
    q = Queue()
    q.queue = q.queue.__class__(l)
    return q


def betterRepr(o):
    # the main difference: this one is deterministic
    # the orig dict.__repr__ has the order undefined.
    if isinstance(o, list):
        return "[\n" + "".join([betterRepr(v) + ",\n" for v in o]) + "]"
    if isinstance(o, deque):
        return "deque([\n" + "".join([betterRepr(v) + ",\n" for v in o]) + "])"
    if isinstance(o, Queue):
        return "loadQueue([\n" + "".join([betterRepr(v) + ",\n" for v in list(o.queue)]) + "])"
    if isinstance(o, tuple):
        return "(" + ", ".join(map(betterRepr, o)) + ")"
    if isinstance(o, dict):
        return "{\n" + "".join([betterRepr(k) + ": " + betterRepr(v) + ",\n" for (k,v) in sorted(o.items())]) + "}"
    if isinstance(o, set):
        return "set([\n" + "".join([betterRepr(v) + ",\n" for v in sorted(o)]) + "])"
    # fallback
    return repr(o)
