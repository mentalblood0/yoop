import pytest

from .. import yoop



@pytest.fixture
def channel():
	return yoop.Playlist(
		yoop.Link('https://www.youtube.com/@KaneB')
	)

def test_title(channel: yoop.Playlist):
	assert channel.title == 'Kane B - Videos'

def test_uploader(channel: yoop.Playlist):
	assert channel.uploader == 'Kane B'