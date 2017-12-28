# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# loosely inspired from https://github.com/albertz/PictureSlider/blob/master/PictureSlider/FileQueue.cpp

import random
import sys
from threading import RLock
from typing import List, Union
import Index


kNonloadedDirsExpectedFac = 0.5
kNonloadedDirsExpectedMin = 100

rndInt = random.randint


class RandomFileQueue:
    def __init__(self, root_dir, filesystem):
        """
        :param Index.Dir root_dir:
        :param Index.Filesystem filesystem:
        """
        root_dir = root_dir.remove_trailing_slash()
        self.root_dir = root_dir
        self.fs = filesystem
        import main
        self.filterBlacklist = lambda l: filter(lambda entry: main.allowed_by_blacklist(entry.url), l)

        class Dir:
            owner = self
            isLoaded = False
            isLoading = False
            base = None  # type: Index.Dir

            def __init__(self):
                self.files = []  # type: List[Index.File]
                self.loadedDirs = []  # type: List[Dir]
                self.nonloadedDirs = []  # type: List[Dir]
                self.lock = RLock()

            def _start_loading(self):
                with self.lock:
                    if self.isLoading:
                        # Don't wait for it.
                        # By throwing this exception, we will get the effect that we will retry later.
                        raise self.owner.fs.TemporaryException("parallel thread is loading dir: %s" % self.base)
                    self.isLoading = True

            def load(self):
                with self.lock:
                    if self.isLoaded:
                        return
                    self._start_loading()
                try:
                    listed_dir = self.owner.fs.list_dir(self.base)
                    listed_dir = self.owner.filterBlacklist(listed_dir)  # type: List[Union[Index.Dir,Index.File]]
                except self.owner.fs.TemporaryException as exc:
                    # try again another time
                    self.isLoading = False
                    raise  # fall down to bottom
                except Exception:
                    self.owner.fs.handle_exception(*sys.exc_info())
                    # This is an unexpected error, which we handle as fatal.
                    # Note that other possible permanent errors (permission error, file not found, or so)
                    # are handled in listDir(), which probably returns also [] then.
                    listed_dir = []
                files = []
                nonloaded_dirs = []
                for f in listed_dir:
                    if self.owner.fs.is_file(f):
                        files += [f]
                    elif self.owner.fs.is_dir(f):
                        subdir = Dir()
                        subdir.base = f
                        nonloaded_dirs += [subdir]
                with self.lock:
                    self.files = files
                    self.nonloadedDirs = nonloaded_dirs
                    self.isLoaded = True
                    self.isLoading = False

            def expected_files_count(self):
                """
                :rtype: int
                """
                c = 0
                c += len(self.files)
                for d in self.loadedDirs:
                    c += d.expected_files_count()
                c += len(self.nonloadedDirs) * \
                    max(int(kNonloadedDirsExpectedFac * c), kNonloadedDirsExpectedMin)
                return c

            def random_get(self):
                """
                :rtype: Index.File|None
                """
                self.load()
                assert self.isLoaded

                while True:
                    rmax = self.expected_files_count()
                    if rmax == 0:
                        return None
                    r = rndInt(0, rmax - 1)

                    if r < len(self.files):
                        return self.files[r]
                    r -= len(self.files)

                    for d in self.loadedDirs:
                        c = d.expected_files_count()
                        if r < c:
                            f = d.random_get()
                            if f:
                                return f
                            r = None
                            break
                        r -= c
                    if r is None:
                        continue

                    # Load any of the nonloadedDirs.

                    with self.lock:
                        if len(self.nonloadedDirs) == 0:
                            continue
                        r = rndInt(0, len(self.nonloadedDirs) - 1)
                        d = self.nonloadedDirs[r]

                    # Don't do in locked state to not hold the lock for too long.
                    d.load()

                    with self.lock:
                        self.nonloadedDirs.remove(d)
                        self.loadedDirs += [d]

        self.root = Dir()
        self.root.base = root_dir

    def get_next_file(self):
        """
        :rtype: Index.File|None
        """
        return self.root.random_get()
