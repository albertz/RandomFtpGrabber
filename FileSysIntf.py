
import ftplib
from urllib.parse import urlparse

def listDir(url):
	"""
	returns tuple of lists: (dirs, files)
	both are absolute urls
	"""
	o = urlparse(url)
	if o.scheme == "ftp":
		return ftpListDir(url)

	raise NotImplementedError

def ftpListDir(url):
	o = urlparse(url)
	ftp = ftplib.FTP()
	kwargs = { "host": o.hostname or o.netloc }
	if o.port: kwargs["port"] = o.port
	ftp.connect(**kwargs)
	kwargs = {}
	if o.username: kwargs["user"] = o.username
	if o.password: kwargs["passwd"] = o.password
	ftp.login(**kwargs)
	ftp.cwd(o.path)

	lines = []
	ftp.dir(o.path, lines.append)
	dirs = []
	files = []
	for line in lines:
		fields = line.split()
		name = ' '.join(fields[8:])
		if line[0] == 'd':
			container = dirs
		elif line[0] == '-':
			container = files
		elif line[0] == 'l':
			continue
		else:
			raise ValueError("Don't know what kind of file I have: %s" % line.strip())
		container.append(url + "/" + name)

	return dirs, files

