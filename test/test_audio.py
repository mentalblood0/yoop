import pytest
import pathlib
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
		channels   = yoop.Audio.Channels.mono
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
def test_audio_converted(format: yoop.Audio.Format):

	bitrate    = yoop.Audio.Bitrate(80)
	samplerate = yoop.Audio.Samplerate(32000)
	channels   = yoop.Audio.Channels.mono

	result = audio().converted(
		bitrate    = bitrate,
		samplerate = samplerate,
		format     = format,
		channels   = channels
	)

	assert result.bitrate    == bitrate
	assert result.samplerate == samplerate
	assert result.format     == format
	assert result.channels   == channels


@pytest.mark.skip(reason = 'expensive in terms of traffic and time')
def test_audio_splitted():

	bitrate    = yoop.Audio.Bitrate(80)
	samplerate = yoop.Audio.Samplerate(32000)
	channels   = yoop.Audio.Channels.mono
	format     = yoop.Audio.Format.MP3

	result = audio().converted(
		bitrate    = bitrate,
		samplerate = samplerate,
		format     = format,
		channels   = channels
	).splitted(3)

	for r in result:
		assert r.bitrate    == bitrate
		assert r.samplerate == samplerate
		assert r.format     == format
		assert r.channels   == channels