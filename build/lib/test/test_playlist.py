import pytest
import functools

from .. import yoop

from .test_channel import channel



@functools.lru_cache
def playlists():
	return yoop.Playlist(channel().url / 'playlists')


@pytest.mark.parametrize(
	'field',
	(
		'id',
		'title',
		'uploader'
	)
)
def test_string_fields(field: str):
	assert isinstance(playlists().__getattribute__(field), str)
	assert len(playlists().__getattribute__(field))


def test_videos():
	for p in playlists():
		assert isinstance(p, yoop.Playlist)