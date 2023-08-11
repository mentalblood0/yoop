import pytest
import functools

from .. import yoop



@pytest.fixture
@functools.cache
def channel():
	return yoop.Playlist(
		yoop.Link('https://www.youtube.com/@KaneB')
	)

def test_title(channel: yoop.Playlist):
	assert channel.title == 'Kane B - Videos'

def test_uploader(channel: yoop.Playlist):
	assert channel.uploader == 'Kane B'