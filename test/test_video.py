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


@functools.lru_cache
def audio():
	return video().audio(yoop.Audio.Bitrate(90))


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio_basic():
	tags = {
		'title': ['lalala']
	}
	result = audio().converted(
		bitrate    = yoop.Audio.Bitrate(75),
		samplerate = yoop.Audio.Samplerate(32000),
		format     = yoop.Audio.Format.MP3,
		channels   = yoop.Audio.Channels.one
	).tagged(**tags)
	for k, v in tags.items():
		assert result.tags[k] == v


# @pytest.mark.skip(reason = 'expensive in terms of traffic and time')
@pytest.mark.parametrize(
	'format',
	(
		f
		for f in yoop.Audio.Format
	)
)
def test_audio_converting(format: yoop.Audio.Format):
	audio().converted(
		bitrate    = yoop.Audio.Bitrate(75),
		samplerate = yoop.Audio.Samplerate(32000),
		format     = format,
		channels   = yoop.Audio.Channels.one
	)