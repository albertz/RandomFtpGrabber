
import os
import re
import time
import Logging


kWgetProgressLineMod = 10
kWgetNumTries = 3
kWgetTimeout = 10  # in secs
kMaxFilenameLenPrint = 15


def _wget_is_progress_line(line):
    """
    :param str line:
    :rtype: bool
    """
    parts = line.split()
    if not parts:
        return False
    first = parts[0]
    if not first:
        return False
    first = first[:-1]  # "K" or so is at the end
    try:
        int(first)
    except ValueError:
        return False
    return True


def convert_to_unicode(value):
    """
    :param str|bytes|unicode value:
    :rtype: str
    """
    if isinstance(value, str):
        return value
    assert isinstance(value, bytes)
    try:
        value = value.decode("utf-8")
    except UnicodeError:
        try:
            value = value.decode()  # default
        except UnicodeError:
            try:
                value = value.decode("iso-8859-1")
            except UnicodeError:
                value = value.decode("utf-8", "replace")
                #value = value.replace(u"\ufffd", "?")
    assert isinstance(value, str)
    return value


class DownloadFatalError(Exception):
    """
    E.g. the file does not exist anymore, or so.
    We should not retry anymore.
    """


class DownloadTemporaryError(Exception):
    """
    We hope that we can still get access to the file at some later point.
    """


class Downloader:
    def __init__(self, url):
        """
        :param str url:
        """
        self.url = url
        self.last_output_time = None

    def __repr__(self):
        return "Downloader(%r)" % self.url

    def describe_state(self):
        if not self.last_output_time:
            return "not started"
        return "last output %f secs ago" % (time.time() - self.last_output_time,)

    def __str__(self):
        return "%r, %s" % (self, self.describe_state())

    def run(self):
        url = self.url
        filename = os.path.basename(str(url))
        filename, ext = os.path.splitext(filename)
        if len(filename) > kMaxFilenameLenPrint:
            filename = filename[:kMaxFilenameLenPrint] + "..."
        filename = filename + ext
        print_prefix = "wget (%s)" % filename
        Logging.log("%s: start download %s" % (print_prefix, url))

        args = ["wget",
                "--continue",
                "--no-check-certificate",  # SSL errors ignored, like in list-dir
                "--force-directories",
                "--directory-prefix", "downloads/",
                "--progress=dot:mega",  # see also the progress handling below
                "--tries=%i" % kWgetNumTries,  # note that we also do our own retry-handling
                "--timeout=%i" % kWgetTimeout,
                str(url)]
        Logging.log(" ".join(map(repr, args)))

        from subprocess import Popen, PIPE, STDOUT
        env = os.environ.copy()
        env["LANG"] = env["LC"] = env["LC_ALL"] = "en_US.UTF-8"
        devnull = open(os.devnull, "rb")
        p = Popen(args, stdin=devnull, stdout=PIPE, stderr=STDOUT, bufsize=0, env=env)

        target_filename = None
        progress_line_idx = 0
        while p.returncode is None:
            line = p.stdout.readline()
            self.last_output_time = time.time()
            line = convert_to_unicode(line)
            line = line.rstrip()
            if not line:
                pass  # Cleanup output a bit.
            elif _wget_is_progress_line(line):
                if progress_line_idx % kWgetProgressLineMod == 0:
                    Logging.log("%s progress: %s" % (print_prefix, line))
                progress_line_idx += 1
            elif line.strip().startswith("=>"):  # => ‘downloads/...’
                m = re.match("\\s*=> ‘(.*)’", line)
                assert m, "%s: unexpected target filename pattern: %r" % (self, line)
                target_filename = m.group(1)
                Logging.log("%s: target filename: %s" % (print_prefix, target_filename))
            elif line.strip().startswith("Saving to:"):  # Saving to: ‘downloads/...’
                m = re.match("\\s*Saving to: ‘(.*)’", line)
                assert m, "%s: unexpected target filename pattern: %r" % (self, line)
                target_filename = m.group(1)
                Logging.log("%s: target filename: %s" % (print_prefix, target_filename))
            else:
                Logging.log("%s: %s" % (print_prefix, line))
                # The only good way to check for certain errors.
                if line.startswith("No such file "):
                    p.kill()
                    raise DownloadFatalError("error: " + line)
                if line.startswith("No such directory "):
                    p.kill()
                    raise DownloadFatalError("error: " + line)
                if "404 Not Found" in line:
                    p.kill()
                    raise DownloadFatalError("error: " + line)
                if "416 Requested Range" in line:
                    p.kill()
                    raise DownloadFatalError("error: " + line)
            p.poll()

        if progress_line_idx > 0:
            assert target_filename and os.path.exists(target_filename)

        if p.returncode != 0:
            if not target_filename or not os.path.exists(target_filename):
                # Just skip it. We might later add it again.
                raise DownloadFatalError("return code %i; download not started" % p.returncode)
            raise DownloadTemporaryError("return code %i; download started" % p.returncode)

        Logging.log("%s done." % print_prefix)
