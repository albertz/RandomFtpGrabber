
"""
For some fun.
"""

import os
import sys
import imp
import Logging

def getLocalModChangeTime(filename):
    return os.path.getmtime(myDir + "/" + filename)

def normModDir(filename):
    return os.path.normpath(os.path.dirname(os.path.abspath(filename)))

myDir = normModDir(__file__)
modChangeTimes = {} # modName -> time

def listLocalModuleNames():
    from glob import glob
    for fn in glob(myDir + "/*.py"):
        fn = os.path.basename(fn)
        modName, _ = os.path.splitext(fn)
        yield modName

def initModChangeTimes():
    for modName in listLocalModuleNames():
        if modName not in modChangeTimes:
            modChangeTimes[modName] = getLocalModChangeTime(modName)

def checkReloadModules():
    initModChangeTimes() # update maybe not-yet-known modules

    for modName in listLocalModuleNames():
        if modName not in modChangeTimes: continue
        if modName not in sys.modules: continue
        lastMtime = modChangeTimes[modName]
        curMtime = getLocalModChangeTime(modName)
        if curMtime > lastMtime:
            mod = sys.modules[modName]
            Logging.log("reload %s" % mod)
            try:
                imp.reload(mod)
            except Exception:
                Logging.log_exception("reloadHandler", *sys.exc_info())

initModChangeTimes()
