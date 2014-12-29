# Random FTP grabber

Situation:
You have various file servers with interesting stuff,
too much which you can possibly download,
and most of the stuff you never heard about so you
cannot tell how much it is of interest,
but you still want to download a good set of files.

(A common such situation is if you are on a
Hacker Conference like the Chaos Communication Congress/Camp.)

A totally random sampling might already be a good enough
representation, but we might be able to improve slightly.

A bit tricky is if there are multiple-parts
which belong together - they should be grabbed together.


## Usage

Go into the directory where you want to download to.

    echo "ftp://bla/blub1" >> sources.txt
    echo "ftp://blub/bla2" >> sources.txt
    mkdir downloads
    RandomFtpGrabber/main.py

It will create some `*.db` files, e.g. `index.db`, where
it saves its current state, so when you kill it and restart it,
it should resume everything, all running downloads and the lazy
indexing.


## Details

* Python 3.
* Downloads via `wget`.
* Provide a list of source URLs in the file `./source.txt`.
* Lazy random sampled indexing of the files.
It doesn't build a full index in the beginning, it rather randomly
browses through the given sources and randomly selects files for download.
See [`RandomFileQueue`](https://github.com/albertz/RandomFtpGrabber/blob/master/RandomFileQueue.py)
for details on the random walking algorithm.
If you run it long enough, it still will end up with a full file index, though.
* FTP indexing via Python `ftplib`. (HTTP is wip).
* Resumes later on temporary problems (connection timeout, FTP error 4xx),
skips dirs/files with unrecoverable problems (file not found anymore or so, FTP error 5xx).
* Multiple worker threads and a task system with a work queue.
See [`TaskSystem`](https://github.com/albertz/RandomFtpGrabber/blob/master/TaskSystem.py)
for details on the implementation.
* Serializes current state (as readable Python expressions)
and will recover it on restart, thus it will resume all current actions such as downloads.
See [`Persistence`](https://github.com/albertz/RandomFtpGrabber/blob/master/Persistence.py)
for details on the implementation.


## Plan

For found files, it should run some detection whether it should be downloaded
(or how to prioritize certain files more than others).

Via the [Python module `guessit`](https://pypi.python.org/pypi/guessit),
we can extract useful information just from
the filename - works well for movies, episodes or music.

We can then use IMDb to get some more information for movies.
The [Python module `IMDbPY`](http://imdbpy.sourceforge.net/)
might be useful for this case
(although it doesn't support Python 3 yet - see
[here](https://github.com/alberanid/imdbpy/issues/17)).
Then, also [this](http://stackoverflow.com/questions/5342329/can-i-retrieve-imdbs-movie-recommendations-for-a-given-movie-using-imdbpy) is relevant.

Some movie recommendation engine can then be useful.

There also could be some movie blacklist. I don't want to download
movies which I already have seen.

There could be other filters.


## Contribute

Do you want to hack on it?
You are very welcome!

About the plans, just contact me so we can do some brainstorming.

Want to support some new protocol?
Modify [`FileSysIntf`](https://github.com/albertz/RandomFtpGrabber/blob/master/FileSysIntf.py)
for the indexing
and [`Downloader`](https://github.com/albertz/RandomFtpGrabber/blob/master/Downloader.py)
for the download logic, although this might already work because it
just uses `wget` for everything.


## Author

Albert Zeyer, [albzey@gmail.com](mailto:albzey@gmail.com).

