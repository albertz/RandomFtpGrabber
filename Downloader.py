
import os

kWgetProgessLineMod = 10
kMaxFilenameLenPrint = 15

def _wget_isProgressLine(line):
	splitted = line.split()
	if not splitted: return False
	first = splitted[0]
	if not first: return False
	first = first[:-1] # "K" or so is at the end
	try: int(first)
	except ValueError: return False
	return True

def convertToUnicode(value):
	"""
	:rtype : str
	"""
	if isinstance(value, str): return value
	assert isinstance(value, bytes)
	try:
		value = value.decode("utf-8")
	except UnicodeError:
		try:
			value = value.decode() # default
		except UnicodeError:
			try:
				value = value.decode("iso-8859-1")
			except UnicodeError:
				value = value.decode("utf-8", "replace")
				#value = value.replace(u"\ufffd", "?")
	assert isinstance(value, str)
	return value

class DownloadError(Exception): pass

def download(url):
	filename = os.path.basename(str(url))
	filename, ext = os.path.splitext(filename)
	if len(filename) > kMaxFilenameLenPrint:
		filename = filename[:kMaxFilenameLenPrint] + "..."
	filename = filename + ext
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
		line = convertToUnicode(line)
		line = line.rstrip()
		if _wget_isProgressLine(line):
			if progressLineIdx % kWgetProgessLineMod == 0:
				print("%s progress: %s" % (printPrefix, line))
			progressLineIdx += 1
		else:
			print("%s: %s" % (printPrefix, line))
		p.poll()
	if p.returncode != 0:
		raise DownloadError("return code %i" % p.returncode)
