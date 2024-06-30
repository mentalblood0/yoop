import functools

import pytest

from .. import yoop


@functools.lru_cache
def channel():
    # return yoop.Playlist(yoop.Url("https://www.youtube.com/@KaneB"))
    return yoop.Playlist(yoop.Url("https://vesselofiniquity.bandcamp.com/music"))


@pytest.mark.parametrize("field", ("id", "title"))
def test_string_fields(field: str):
    assert isinstance(channel().__getattribute__(field), str)
    assert len(channel().__getattribute__(field))
    for p in channel():
        print(p)
        for s in p:
            print(s)
    assert False
