
import re
from collections import deque
from queue import Queue


def isPythonReprFormat(filename):
	f = open(filename, "rb")
	try:
		firstByte = str(f.read(1))
	except UnicodeDecodeError:
		return False
	# List, dict, tuple, string or number.
	if firstByte in "[{(\"'0123456789-":
		return True
	f.seek(0)
	try:
		beginning = str(f.read(100))
	except UnicodeDecodeError:
		return False
	# Maybe some identifier.
	if re.match("[_A-Za-z][_a-zA-Z0-9.]*\(", beginning):
		return True
	return False

def loadPythonReprFormat(filename):
	code = open(filename, "r").read()
	return eval(code)


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
