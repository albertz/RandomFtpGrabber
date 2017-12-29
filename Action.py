
from RandomFileQueue import RandomFileQueue
from weakref import WeakKeyDictionary
from threading import RLock
import Downloader
import TaskSystem
import Index
import FileSysIntf
import Logging
from typing import Dict


lock = RLock()
randomWalkers = WeakKeyDictionary()  # type: Dict[Index.Dir,RandomFileQueue]


def get_random_walker(base):
    """
    :param Index.Dir base:
    :rtype: RandomFileQueue
    """
    with lock:
        if base in randomWalkers:
            return randomWalkers[base]
        walker = RandomFileQueue(root_dir=base, filesystem=Index.filesystem)
        randomWalkers[base] = walker
        return walker


class BaseAction:
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return self.__class__.__name__ < other.__class__.__name__
        return id(self) < id(other)

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class Download(BaseAction):
    def __init__(self, url):
        self.url = str(url)
        self.downloader = Downloader.Downloader(url=self.url)

    def __call__(self):
        import main
        if not main.allowed_by_blacklist(self.url):
            return
        try:
            self.downloader.run()
        except Downloader.DownloadTemporaryError:
            # Retry later.
            # However, also queue some random action to allow other downloads.
            TaskSystem.queue_work(RandomNextFile())
            TaskSystem.queue_work(self)
        except Downloader.DownloadFatalError:
            # Cannot handle. Nothing we can do.
            pass

    def __hash__(self):
        return hash(str(self.url))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return str(self.url) == str(other.url)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return self.__class__.__name__ < other.__class__.__name__
        return str(self.url) < str(other.url)

    def __repr__(self):
        return "Download(%r)" % str(self.url)


class RandomNextFile(BaseAction):
    """
    This will search through the sources, via :func:`get_random_walker`,
    which will lazily build up the file index and explore all the directories,
    and add some random file to the download queue.
    """
    def __init__(self, base=None, url=None):
        """
        :param None|Index.Dir base:
        :param None|str url:
        """
        if url:
            assert not base
            base = Index.Dir(url=url)
        if not base:
            base = Index.index.get_random_source()  # type: Index.Dir
        self.base = base

    def __call__(self):
        walker = get_random_walker(self.base)
        try:
            # Either throws TemporaryException or returns None if empty.
            url = walker.get_next_file()
        except FileSysIntf.TemporaryException as exc:
            # Handle another one later.
            # Will automatically be added.
            Logging.log("%s: TemporaryException:" % self, exc)
            return
        if not url:
            # Can happen if we end up in an empty source or directory.
            Logging.log("%s: no file found" % self)
            Index.index.remove_source(self.base)
            return
        if TaskSystem.reached_suggested_max_queue():
            # Better go exploring a bit more, and handle the current queue first.
            Logging.log("%s: reached suggested max queue, will not queue download" % self)
            return
        TaskSystem.queue_work(Download(url))

    def __hash__(self):
        return hash(str(self.base.url))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return str(self.base.url) == str(other.base.url)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return self.__class__.__name__ < other.__class__.__name__
        return str(self.base.url) < str(other.base.url)

    def __repr__(self):
        # Doesn't matter which base, just take another random next time.
        # This repr will be used for the persistence storage.
        return "RandomNextFile()"

    def __str__(self):
        return "RandomNextFile{%r}" % self.base.url


class CheckDownloadsFinished(BaseAction):
    """ If we download the remaining files, check if we are finished """

    def __call__(self):
        import main
        if not main.DownloadOnly:
            # This can happen if we saved this action at an earlier run
            # where we had the option enabled.
            # Just ignore it now.
            return
        import TaskSystem
        import Threading
        # Check if there are no more downloads running.
        if len(TaskSystem.currentWork) <= 1:  # should only be ourselves
            # Exit.
            Logging.log("All downloads finished.")
            Threading.do_in_main_thread(IssueSystemExit(), wait=False)
        else:
            # Check again later.
            TaskSystem.queue_work(CheckDownloadsFinished())


class IssueSystemExit(BaseAction):
    def __call__(self):
        Logging.log("Exit now.")
        raise SystemExit


def get_new_action():
    return RandomNextFile()

