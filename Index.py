
import Persistence
import FileSysIntf
from Threading import synced_on_obj
import random
import Logging
from typing import Dict


# Interface for RandomFileQueue
class Filesystem:
    def list_dir(self, path):
        """
        :param Dir path:
        :rtype: list[Dir|File]
        """
        return path.list_dir()

    def is_file(self, path):
        """
        :param Dir|File path:
        :rtype: bool
        """
        return isinstance(path, File)

    def is_dir(self, path):
        """
        :param Dir|File path:
        :rtype: bool
        """
        return isinstance(path, Dir)

    def handle_exception(self, exctype, value, traceback):
        Logging.log_exception("Filesystem", exctype, value, traceback)

    TemporaryException = FileSysIntf.TemporaryException


class FileBase:
    def __init__(self, url):
        """
        :param str url:
        """
        self.url = url

    def __str__(self):
        return self.url


class File(FileBase):
    def __repr__(self):
        return "File(%r)" % self.url


class Dir(FileBase):
    def __init__(self, url, children=None):
        """
        :param str url:
        :param None|list[Dir|File] children:
        """
        super().__init__(url)
        self.children = children
        self.lastException = None

    @synced_on_obj
    def list_dir(self):
        """
        :rtype: list[Dir|File]
        """
        if self.children is not None:
            return self.children

        Logging.log("listDir: %s" % self.url)

        try:
            dirs, files = FileSysIntf.list_dir(self.url.rstrip("/"))
        except FileSysIntf.TemporaryException as e:
            Logging.log("ListDir temporary exception on %s:" % self.url, str(e) or type(e))
            # Reraise so that the outer caller gets noticed that it can retry later.
            raise
        except Exception as e:
            Logging.log("ListDir unrecoverable exception on %s:" % self.url, str(e) or type(e))
            self.lastException = e
            self.children = []
            return []

        self.children = \
            list(map(Dir, dirs)) + \
            list(map(File, files))
        # noinspection PyUnresolvedReferences
        index.save()

        # By raising TemporaryException here, it will have the effect that we will try again later.
        raise FileSysIntf.TemporaryException("queried one list-dir, do more next round")

    def __str__(self):
        return self.url

    def __repr__(self):
        return "Dir(%r, %s)" % (self.url, Persistence.better_repr(self.children))


class Index:
    def __init__(self, sources=None):
        """
        :param None|dict[str,Dir] sources:
        """
        self.sources = sources or {}  # type: Dict[str,Dir]
        self._load_sources()
        import main
        main.reloadHandlers += [self._load_sources]

    def _load_sources(self):
        import main
        for source in main.Sources:
            if source not in self.sources:
                self.sources[source] = Dir(url=source)
        for source in list(self.sources.keys()):
            if source not in main.Sources:
                del self.sources[source]

    def get_random_source(self):
        """
        :rtype: Dir
        """
        return random.choice(list(self.sources.values()))

    def get_source(self, source):
        """
        :param str source:
        :rtype: Dir
        """
        return self.sources[source]

    def __repr__(self):
        return "Index(%s)" % Persistence.better_repr(self.sources)


filesystem = Filesystem()

index = Persistence.load("index.db", Index)
