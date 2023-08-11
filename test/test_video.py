import pytest

from .. import yoop

from .test_channel import channel



@pytest.fixture
def video(channel: yoop.Playlist):
	return yoop.Video(channel[0])

@pytest.mark.parametrize(
	'field',
	(
		'id',
		'title',
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
	assert isinstance(video.__getitem__(field), str)
	assert len(video.__getitem__(field))