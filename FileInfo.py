
import sys
import Logging

try:
    import guessit
except ImportError:
    print("failed to import guessit:")
    Logging.log_exception(*sys.exc_info())
    print("This is mandatory. Please install via PIP")
    print("pip3 install guessit")
    sys.exit(-1)


def get_info(url):
    return guessit.guess_file_info(filename=url)

