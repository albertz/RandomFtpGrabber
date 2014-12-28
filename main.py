#!/usr/bin/env python3

import better_exchook
better_exchook.install()

import sys
from argparse import ArgumentParser
import os

RootDir = None
Sources = None

def init(*rawArgList):
	argParser = ArgumentParser()
	argParser.add_argument("--dir", default=os.getcwd())
	args = argParser.parse_args(rawArgList)

	global RootDir
	RootDir = args.dir
	print("root dir: %s" % RootDir)

	global Sources
	Sources = open(RootDir + "/sources.txt").read().splitlines()



if __name__ == "__main__":
	import main
	main.init(*sys.argv[1:])
	try:
		import TaskSystem # important to be initially imported in the main thread
		TaskSystem.mainLoop()
	except KeyboardInterrupt:
		print("KeyboardInterrupt")
