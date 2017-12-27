#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import os
import termios
import re


RootDir = "."
Sources = []
Blacklist = []
DownloadOnly = False
Args = None
reloadHandlers = []


def printStdinHelp():
    print("Console control:")
    print("  <r>:  reload lists (sources, blacklist)")
    print("  <q>:  quit")


def prepareStdin():
    fd = sys.stdin.fileno()

    if os.isatty(fd):
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
        # http://www.unixguide.net/unix/programming/3.6.2.shtml
        new[6][termios.VMIN] = 0
        new[6][termios.VTIME] = 1  # timeout

        termios.tcsetattr(fd, termios.TCSANOW, new)
        termios.tcsendbreak(fd, 0)

        import atexit
        atexit.register(lambda: termios.tcsetattr(fd, termios.TCSANOW, old))

        printStdinHelp()

    else:
        print("Not a tty. No stdin control.")


def stdinGetChar():
    fd = sys.stdin.fileno()
    ch = os.read(fd, 7)
    return ch


def stdinHandlerLoop():
    while True:
        ch = stdinGetChar()
        if not ch:
            continue
        elif ch == b"q":
            print("Exit.")
            import Threading
            from Action import IssueSystemExit
            Threading.doInMainthread(IssueSystemExit(), wait=False)
            return
        elif ch == b"r":
            print("Reload lists.")
            setupLists()
            for handler in reloadHandlers:
                handler()
        else:
            print("Unknown key command: %r" % ch)
            printStdinHelp()


def startStdinHandlerLoop():
    prepareStdin()

    from threading import Thread
    t = Thread(target=stdinHandlerLoop, name="stdin control")
    t.daemon = True
    t.start()


def setupLists():
    main.Sources = open(RootDir + "/sources.txt").read().splitlines()
    if os.path.exists(RootDir + "/blacklist.txt"):
        blacklist = open(RootDir + "/blacklist.txt").read().splitlines()
        main.Blacklist = [re.compile(bad_pattern) for bad_pattern in blacklist]
    else:
        main.Blacklist = []


def allowedByBlacklist(entry):
    for bad_pattern_re in main.Blacklist:
        if bad_pattern_re.match(entry):
            return False
    return True


def setup(*rawArgList):
    print("RandomFtpGrabber startup.")

    import better_exchook
    better_exchook.install()
    import Logging
    better_exchook.output = Logging.log

    argParser = ArgumentParser()
    argParser.add_argument("--dir", default=os.getcwd())
    argParser.add_argument("--numWorkers", type=int)
    argParser.add_argument("--shell", action="store_true")
    argParser.add_argument("--downloadRemaining", action="store_true")
    global Args
    Args = argParser.parse_args(rawArgList)

    if sys.version_info.major != 3:
        Logging.log("Warning: This code was only tested with Python3.")

    startStdinHandlerLoop()

    import main
    main.RootDir = Args.dir
    Logging.log("root dir: %s" % RootDir)

    main.DownloadOnly = Args.downloadRemaining
    if not main.DownloadOnly:
        setupLists()

    import TaskSystem # important to be initially imported in the main thread
    if Args.numWorkers:
        TaskSystem.kNumWorkers = Args.numWorkers
    if Args.shell:
        TaskSystem.kNumWorkers = 0
    TaskSystem.setup()


def mainEntry():
    import TaskSystem
    import Logging
    try:
        TaskSystem.mainLoop()
    except KeyboardInterrupt:
        Logging.log("KeyboardInterrupt")


# Has the effect that this module is know as 'main' and not just '__main__'.
import main

if __name__ == "main":
    setup(*sys.argv[1:])

elif __name__ == "__main__":
    if main.Args.shell:
        import better_exchook
        better_exchook.debug_shell(globals(), globals())
        sys.exit()
    main.mainEntry()

