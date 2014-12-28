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

## Implementation

Python.
Should support resuming.
FTP, HTTP and maybe others.

## Usage

Go into the directory where you want to download to.

    echo "ftp://bla/blub1" >> sources.txt
    echo "ftp://blub/bla2" >> sources.txt
    mkdir downloads
    RandomFtpGrabber/main.py

