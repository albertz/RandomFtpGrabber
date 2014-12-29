#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import os

RootDir = "."
Sources = []

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

	import main
	main.RootDir = args.dir
	Logging.log("root dir: %s" % RootDir)

	main.Sources = open(RootDir + "/sources.txt").read().splitlines()

	import TaskSystem # important to be initially imported in the main thread
	TaskSystem.setup()


def mainEntry(*rawArgList):
	init(*rawArgList)

	import TaskSystem
	import Logging
	try:
		TaskSystem.mainLoop()
	except KeyboardInterrupt:
		Logging.log("KeyboardInterrupt")


if __name__ == "__main__":
	import main
	main.mainEntry(*sys.argv[1:])

