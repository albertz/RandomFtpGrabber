# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# loosely inspired from https://github.com/albertz/PictureSlider/blob/master/PictureSlider/FileQueue.cpp

import random
import sys
from threading import RLock

kNonloadedDirsExpectedFac = 0.5
kNonloadedDirsExpectedMin = 100

rndInt = random.randint


class RandomFileQueue:
    def __init__(self, root_dir, filesystem):
        """
        :param Index.Dir root_dir:
        :param Index.Filesystem filesystem:
        """
        self.root_dir = root_dir
        self.fs = filesystem
        import main
        self.filterBlacklist = lambda l: filter(lambda entry: main.allowed_by_blacklist(entry.url), l)

        class Dir:
            owner = self
            isLoaded = False
            isLoading = False
            base = None

            def __init__(self):
                self.files = []
                self.loadedDirs = []
                self.nonloadedDirs = []
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
                    if self.isLoaded: return
                    self._start_loading()
                try:
                    listed_dir = self.owner.fs.list_dir(self.base)
                    listed_dir = self.owner.filterBlacklist(listed_dir)
                except self.owner.fs.TemporaryException:
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
                nonloadedDirs = []
                for f in listed_dir:
                    if self.owner.fs.is_file(f):
                        files += [f]
                    elif self.owner.fs.is_dir(f):
                        subdir = Dir()
                        subdir.base = f
                        nonloadedDirs += [subdir]
                with self.lock:
                    self.files = files
                    self.nonloadedDirs = nonloadedDirs
                    self.isLoaded = True
                    self.isLoading = False

            def expected_files_count(self):
                c = 0
                c += len(self.files)
                for d in self.loadedDirs:
                    c += d.expected_files_count()
                c += len(self.nonloadedDirs) * \
                    max(int(kNonloadedDirsExpectedFac * c), kNonloadedDirsExpectedMin)
                return c

            def random_get(self):
                self.load()
                assert self.isLoaded

                while True:
                    rmax = self.expected_files_count()
                    if rmax == 0: return None
                    r = rndInt(0, rmax - 1)

                    if r < len(self.files):
                        return self.files[r]
                    r -= len(self.files)

                    for d in self.loadedDirs:
                        c = d.expected_files_count()
                        if r < c:
                            f = d.random_get()
                            if f: return f
                            r = None
                            break
                        r -= c
                    if r is None: continue

                    # Load any of the nonloadedDirs.

                    self._start_loading()
                    with self.lock:
                        assert len(self.nonloadedDirs) > 0
                        r = rndInt(0, len(self.nonloadedDirs) - 1)
                        d = self.nonloadedDirs[r]
                        self.nonloadedDirs = self.nonloadedDirs[:r] + self.nonloadedDirs[r+1:]

                    # Don't do in locked state to not hold the lock for too long.
                    d.load()

                    with self.lock:
                        self.loadedDirs += [d]
                        self.isLoading = False

        self.root = Dir()
        self.root.base = root_dir

    def get_next_file(self):
        return self.root.random_get()
