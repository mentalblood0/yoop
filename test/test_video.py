import pytest

from .. import yoop

from .test_channel import channel



@pytest.fixture
def video(channel: yoop.Playlist):
	return yoop.Video(channel[0])

def test_title(video: yoop.Video):
	assert video.title == 'Philosophical Pessimism'

def test_channel(video: yoop.Video):
	assert video.channel == 'Kane B'