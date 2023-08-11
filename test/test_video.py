import pytest
import functools

from .. import yoop

from .test_channel import channel



@pytest.fixture
@functools.cache
def video(channel: yoop.Playlist):
	return yoop.Video(channel[0])


@pytest.mark.parametrize(
	'field',
	(
		'id',
		'extension',
		'channel',
		'uploader',
		'creator',
		'description',
		'license',
		'location'
	)
)
def test_string_fields(video: yoop.Video, field: str):
	assert isinstance(video.__getattribute__(field), str)
	assert len(video.__getattribute__(field))


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_data(video: yoop.Video):
	assert len(video.data)