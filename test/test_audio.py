import pytest
import functools

from .. import yoop

from .test_video import video



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


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
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