

def download(url):
	print("download: %s" % url)

	args = ["wget",
			"--continue",
			"--force-directories",
			"--directory-prefix", "downloads/",
			str(url)]
	print(" ".join(map(repr, args)))

	from subprocess import Popen
	p = Popen(args)
	p.wait()
	if p.returncode != 0:
		raise Exception("error while downloading")
