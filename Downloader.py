
import os

kWgetProgessLineMod = 10

def _wget_isProgressLine(line):
	splitted = line.split()
	if not splitted: return False
	first = splitted[0]
	if not first: return False
	first = first[:-1] # "K" or so is at the end
	try: int(first)
	except ValueError: return False
	return True


def download(url):
	filename = os.path.basename(str(url))
	printPrefix = "wget (%s)" % filename
	print("%s: start download %s" % (printPrefix, url))

	args = ["wget",
			"--continue",
			"--force-directories",
			"--directory-prefix", "downloads/",
			"--progress=dot:mega",
			str(url)]
	print(" ".join(map(repr, args)))

	from subprocess import Popen, PIPE, STDOUT, DEVNULL
	p = Popen(args, stdin=DEVNULL, stdout=PIPE, stderr=STDOUT, bufsize=0)
	progressLineIdx = 0
	while p.returncode is None:
		line = p.stdout.readline()
		if _wget_isProgressLine(line):
			if progressLineIdx % kWgetProgessLineMod == 0:
				print("%s progress: %s" % (printPrefix, line))
			progressLineIdx += 1
		else:
			print("%s: %s" % (printPrefix, line))
		p.poll()
	if p.returncode != 0:
		raise Exception("error while downloading")
