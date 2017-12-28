
from Action import *


def test_RandomNextFile_hashable():
    rnf1 = RandomNextFile(url="http://localhost")
    rnf2 = RandomNextFile(url="http://localhost")
    rnf3 = RandomNextFile(url="http://www.google.com")
    assert rnf1 == rnf2
    assert hash(rnf1) == hash(rnf2)
    assert rnf1 != rnf3
    assert hash(rnf1) != hash(rnf3)
    s = set()
    s.add(rnf1)
    assert rnf2 in s
    assert rnf3 not in s


def test_Download_hashable():
    a1 = Download(url="http://localhost")
    a2 = Download(url="http://localhost")
    a3 = Download(url="http://www.google.com")
    assert a1 == a2
    assert hash(a1) == hash(a2)
    assert a1 != a3
    assert hash(a1) != hash(a3)
    s = set()
    s.add(a1)
    assert a2 in s
    assert a3 not in s
