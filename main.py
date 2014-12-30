#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import os

RootDir = "."
Sources = []
DownloadOnly = False
Args = None

def setup(*rawArgList):
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

	import main
	main.RootDir = Args.dir
	Logging.log("root dir: %s" % RootDir)

	main.DownloadOnly = Args.downloadRemaining
	if not main.DownloadOnly:
		main.Sources = open(RootDir + "/sources.txt").read().splitlines()

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

