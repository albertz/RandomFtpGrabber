
import os
import Logging

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

class DownloadFatalError(Exception): pass
class DownloadTemporaryError(Exception): pass

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
            "--no-check-certificate",  # SSL errors ignored, like in list-dir
            "--force-directories",
            "--directory-prefix", "downloads/",
            "--progress=dot:mega", # see also the progress handling below
            "--tries=5", # note that we also do our own retry-handling
            str(url)]
    print(" ".join(map(repr, args)))

    from subprocess import Popen, PIPE, STDOUT
    env = os.environ.copy()
    env["LANG"] = env["LC"] = env["LC_ALL"] = "en_US.UTF-8"
    devnull = open(os.devnull, "rb")
    p = Popen(args, stdin=devnull, stdout=PIPE, stderr=STDOUT, bufsize=0, env=env)

    progressLineIdx = 0
    while p.returncode is None:
        line = p.stdout.readline()
        line = convertToUnicode(line)
        line = line.rstrip()
        if not line: continue # Cleanup output a bit.
        if _wget_isProgressLine(line):
            if progressLineIdx % kWgetProgessLineMod == 0:
                Logging.log("%s progress: %s" % (printPrefix, line))
            progressLineIdx += 1
        else:
            Logging.log("%s: %s" % (printPrefix, line))
            # The only good way to check for certain errors.
            if line.startswith("No such file "):
                p.kill()
                raise DownloadFatalError("error: " + line)
            if line.startswith("No such directory "):
                p.kill()
                raise DownloadFatalError("error: " + line)
        p.poll()

    if p.returncode != 0:
        raise DownloadTemporaryError("return code %i" % p.returncode)

    Logging.log("%s done." % printPrefix)

