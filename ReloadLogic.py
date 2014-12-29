
"""
For some fun.
"""

import os
import sys
import imp
import Logging

def getModChangeTime(mod):
	return os.path.getmtime(mod.__file__)

def normModDir(filename):
	return os.path.normpath(os.path.dirname(os.path.abspath(filename)))

myDir = normModDir(__file__)
modChangeTimes = {} # mod -> time

def listLocalModules():
	for mod in sys.modules.values():
		if not hasattr(mod, "__file__"): continue
		modDir = normModDir(mod.__file__)
		if modDir == myDir:
			yield mod

def initModChangeTimes():
	for mod in listLocalModules():
		if mod not in modChangeTimes:
			modChangeTimes[mod] = getModChangeTime(mod)

def checkReloadModules():
	initModChangeTimes() # update maybe not-yet-known modules

	for mod in listLocalModules():
		if mod not in modChangeTimes: continue
		lastMtime = modChangeTimes[mod]
		curMtime = getModChangeTime(mod)
		if curMtime > lastMtime:
			Logging.log("reload %s" % mod)
			try:
				imp.reload(mod)
			except Exception:
				Logging.logException("reloadHandler", *sys.exc_info())

initModChangeTimes()
