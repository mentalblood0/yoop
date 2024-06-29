import pytest
import functools

from .. import yoop


@functools.lru_cache
def channel():
    return yoop.Playlist(yoop.Url("https://www.youtube.com/@KaneB"))


@pytest.mark.parametrize("field", ("id", "title"))
def test_string_fields(field: str):
    assert isinstance(channel().__getattribute__(field), str)
    assert len(channel().__getattribute__(field))
