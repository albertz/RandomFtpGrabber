
import os
import time
import ftplib
from urllib.parse import urlparse as urllib_urlparse
import urllib3
import bs4 as BeautifulSoup

http = urllib3.PoolManager()

def urlparse(url):
    return urllib_urlparse(url, allow_fragments=False)

kMaxFtpDepth = 10

class OtherException(Exception): pass
class TemporaryException(Exception): pass


def listDir(url):
    """
    :type url: str
    :returns: tuple of lists: (dirs, files). both are absolute urls
    :rtype: (list[str],list[str])
    """
    o = urlparse(url)
    if o.scheme == "ftp":
        try:
            return ftpListDir(url)
        except ftplib.error_temp as exc:
            time.sleep(1) # sleep to not hammer too much
            raise TemporaryException(exc)
        except ftplib.Error as exc:
            # All others are probably errors where we cannot recover from.
            # Most common are some sort of 5xx errors (no such file etc).
            # However, some FTP servers wrongly classify certain errors,
            # and we check for them first.
            if "the maximum number of allowed clients" in str(exc):
                time.sleep(1) # sleep to not hammer too much
                raise TemporaryException(exc)
            raise OtherException(exc)
        except ftplib.all_errors as exc:
            # These might be network errors, etc.
            # This is very much temporary.
            raise TemporaryException("undefined other expected: %s" % (str(exc) or repr(exc)))
    elif o.scheme in ('http', 'https'):
        return httpListDir(url)
    
    raise NotImplementedError


def ftpListDir(url):
    o = urlparse(url)
    ftp = ftplib.FTP()

    kwargs = { "host": o.hostname or o.netloc }
    if o.port: kwargs["port"] = o.port
    ftp.connect(**kwargs)

    if len(os.path.normpath(o.path).split("/")) > kMaxFtpDepth:
        raise OtherException("max ftp depth reached in %r" % url)

    with ftp:
        kwargs = {}
        if o.username: kwargs["user"] = o.username
        if o.password: kwargs["passwd"] = o.password

        ftp.login(**kwargs)
        path = o.path
        if path[:1] != "/": path = "/" + path # add leading slash
        while path[1:2] == "/": # remove leading double slashes
            path = path[1:]
        path = os.path.normpath(path)
        if len(path) > 1 and path[-1:] == "/": path = path[:-1] # remove trailing slash
        ftp.cwd(path)
        curPwd = ftp.pwd()
        if curPwd != path:
            raise OtherException("path doesnt match: %r vs pwd %r" % (path, curPwd))

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


def _getBaseUrl(url):
    """
    :type url: str
    """
    if url.endswith('/'):
        return url
    start_idx = url.index('://') + len('://')
    if '/' not in url[start_idx:]:  # Just 'http://domain.com'.
        return url + '/'
    return url[:url.rindex('/') + 1]


def httpListDir(url):
    base_url = _getBaseUrl(url)
    r = http.request('GET', url)
    if r.status != 200:
        raise OtherException("HTTP Return code %i, reason: %s" % (r.status, r.reason))
    bs = BeautifulSoup.BeautifulSoup(r.data)  # Parse.

    # This is just a good heuristic.
    dirs = []
    files = []
    for suburl in [anchor['href'] for anchor in bs.findAll('a', href=True)]:
        # Take all relative paths only.
        if ':' in suburl: continue
        if suburl.startswith('/'): continue
        if suburl.startswith('.'): continue
        # Ignore any starting with '?' such as '?C=N;O=D'.
        if suburl.startswith('?'): continue
        # Ending with '/' is probably a dir.
        if suburl.endswith('/'):
            dirs += [base_url + suburl]
        else:
            files += [base_url + suburl]

    return dirs, files
