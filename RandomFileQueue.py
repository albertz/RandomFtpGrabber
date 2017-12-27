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
    def __init__(self, rootdir, filesystem):
        """
        :type rootdir: Index.Dir
        :type filesystem: Index.Filesystem
        """
        self.rootdir = rootdir
        self.fs = filesystem
        import main
        self.filterBlacklist = lambda l: filter(lambda entry: main.allowedByBlacklist(entry.url), l)

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

            def _startLoading(self):
                with self.lock:
                    if self.isLoading:
                        # Don't wait for it.
                        # By throwing this exception, we will get the effect that we will retry later.
                        raise self.owner.fs.TemporaryException("parallel thread is loading dir: %s" % self.base)
                    self.isLoading = True

            def load(self):
                with self.lock:
                    if self.isLoaded: return
                    self._startLoading()
                try:
                    listeddir = self.owner.fs.listDir(self.base)
                    listeddir = self.owner.filterBlacklist(listeddir)
                except self.owner.fs.TemporaryException:
                    # try again another time
                    self.isLoading = False
                    raise # fall down to bottom
                except Exception:
                    self.owner.fs.handleException(*sys.exc_info())
                    # This is an unexpected error, which we handle as fatal.
                    # Note that other possible permanent errors (permission error, file not found, or so)
                    # are handled in listDir(), which probably returns also [] then.
                    listeddir = []
                files = []
                nonloadedDirs = []
                for f in listeddir:
                    if self.owner.fs.isFile(f):
                        files += [f]
                    elif self.owner.fs.isDir(f):
                        subdir = Dir()
                        subdir.base = f
                        nonloadedDirs += [subdir]
                with self.lock:
                    self.files = files
                    self.nonloadedDirs = nonloadedDirs
                    self.isLoaded = True
                    self.isLoading = False

            def expectedFilesCount(self):
                c = 0
                c += len(self.files)
                for d in self.loadedDirs:
                    c += d.expectedFilesCount()
                c += len(self.nonloadedDirs) * \
                    max(int(kNonloadedDirsExpectedFac * c), kNonloadedDirsExpectedMin)
                return c

            def randomGet(self):
                self.load()
                assert self.isLoaded

                while True:
                    rmax = self.expectedFilesCount()
                    if rmax == 0: return None
                    r = rndInt(0, rmax - 1)
                    
                    if r < len(self.files):
                        return self.files[r]
                    r -= len(self.files)
                    
                    for d in self.loadedDirs:
                        c = d.expectedFilesCount()
                        if r < c:
                            f = d.randomGet()
                            if f: return f
                            r = None
                            break
                        r -= c
                    if r is None: continue

                    # Load any of the nonloadedDirs.

                    self._startLoading()
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
        self.root.base = rootdir
        
    def getNextFile(self):
        return self.root.randomGet()
