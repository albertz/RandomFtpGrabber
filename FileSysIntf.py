
import time
import ftplib
from urllib.parse import urlparse

class OtherException(Exception): pass
class TemporaryException(Exception): pass

def listDir(url):
	"""
	returns tuple of lists: (dirs, files)
	both are absolute urls
	"""
	o = urlparse(url)
	if o.scheme == "ftp":
		try:
			return ftpListDir(url)
		except ftplib.error_temp as exc:
			time.sleep(1) # sleep to not hammer too much
			raise TemporaryException(exc)
		except ftplib.Error as exc:
			raise OtherException(exc)
		except ftplib.all_errors as exc:
			# These might be network errors, etc.
			# This is very much temporary.
			raise TemporaryException("undefined other expected: %s" % str(exc) or repr(exc))

	raise NotImplementedError

def ftpListDir(url):
	o = urlparse(url)
	ftp = ftplib.FTP()

	kwargs = { "host": o.hostname or o.netloc }
	if o.port: kwargs["port"] = o.port
	ftp.connect(**kwargs)

	with ftp:
		kwargs = {}
		if o.username: kwargs["user"] = o.username
		if o.password: kwargs["passwd"] = o.password

		ftp.login(**kwargs)
		ftp.cwd(o.path)

		lines = []
		ftp.dir(o.path, lines.append)
		if not lines: return [], []

		if "<DIR>" in lines[0] or lines[0][:1] not in "d-l":
			return _ftpListDirWindows(url, lines)
		else:
			return _ftpListDirUnix(url, lines)

# thanks https://github.com/laserson/ftptree/blob/master/crawltree.py

def _ftpListDirUnix(url, lines):
	dirs, files = [], []

	for line in lines:
		if not line: continue
		fields = line.split()
		if len(fields) < 9:
			raise ValueError("Unix listing, unexpected line, too few fields: %r" % line)
		name = ' '.join(fields[8:])
		if line[0] == 'd':
			container = dirs
		elif line[0] == '-':
			container = files
		elif line[0] == 'l':
			continue
		else:
			raise ValueError("Unix listing, unexpected line, type: %r" % line)
		container.append(url + "/" + name)

	return dirs, files

def _ftpListDirWindows(url, lines):
	dirs, files = [], []

	for line in lines:
		if not line: continue
		fields = line.split()
		if len(fields) < 4:
			raise ValueError("Windows listing, unexpected line, too few fields: %r" % line)
		name = ' '.join(fields[3:])
		if fields[2].strip() == '<DIR>':
			container = dirs
		else:
			container = files
		container.append(url + "/" + name)

	return dirs, files

