import pytest
import functools

from .. import yoop

from .test_channel import channel



@functools.lru_cache
def video():
	return channel()[0]


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
def test_string_fields(field: str):
	assert isinstance(video().__getattribute__(field), str)
	assert len(video().__getattribute__(field))


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_data():
	assert len(video().data)


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio():
	assert len(video().audio())

@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio_bitrate_limit():
	assert len(video().audio(limit = yoop.Audio.Bitrate(90)))