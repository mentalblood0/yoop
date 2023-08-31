import pytest
import functools

from .. import yoop

from .test_channel import channel



@functools.lru_cache
def video():
	match (result := channel()[0]):
		case yoop.Video():
			return result
		case _:
			raise ValueError


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
	value = getattr(video(), field)
	assert isinstance(value, str)
	assert len(value)


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_data():
	assert len(video().data)


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio():
	audio = video().audio(yoop.Audio.Bitrate(90))
	assert len(audio)
	assert audio.converted.tagged(title = 'lalala').tags['title'] == ['lalala']

@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio_bitrate_limit():
	assert len(video().audio(limit = yoop.Audio.Bitrate(90)))