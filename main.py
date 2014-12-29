#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import os

RootDir = None
Sources = None

def init(*rawArgList):
	import better_exchook
	better_exchook.install()
	import Logging
	better_exchook.output = Logging.log

	argParser = ArgumentParser()
	argParser.add_argument("--dir", default=os.getcwd())
	args = argParser.parse_args(rawArgList)

	if sys.version_info.major != 3:
		Logging.log("Warning: This code was only tested with Python3.")

	global RootDir
	RootDir = args.dir
	Logging.log("root dir: %s" % RootDir)

	global Sources
	Sources = open(RootDir + "/sources.txt").read().splitlines()


def mainEntry(*rawArgList):
	init(*rawArgList)

	import Logging
	try:
		import TaskSystem # important to be initially imported in the main thread
		TaskSystem.mainLoop()
	except KeyboardInterrupt:
		Logging.log("KeyboardInterrupt")


if __name__ == "__main__":
	import main
	main.mainEntry(*sys.argv[1:])

