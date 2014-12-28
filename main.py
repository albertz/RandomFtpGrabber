#!/usr/bin/env python3

from argparse import ArgumentParser
import sys
import os
from pprint import pprint

try:
	import guessit
except ImportError:
	print("failed to import guessit:")
	sys.excepthook(*sys.exc_info())
	print("This is mandatory. Please install via PIP")
	print("pip3 install guessit")
	sys.exit(-1)

argParser = ArgumentParser()
argParser.add_argument("--dir", default=os.getcwd())
args = argParser.parse_args()

rootDir = args.dir
print("root dir: %s" % rootDir)

sources = open(rootDir + "/sources.txt").read().splitlines()
print("sources:")
pprint(sources)

pprint(guessit.guess_file_info("Breaking.Bad.S05E08.720p.MP4.BDRip.[KoTuWa].mkv"))

while True:
	pass


