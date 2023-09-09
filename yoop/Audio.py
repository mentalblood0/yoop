import re
import io
import math
import enum
import pytags
import functools
import subprocess
import dataclasses
import mutagen.mp3
import mutagen.id3
import mutagen.easyid3



@dataclasses.dataclass(frozen = True, kw_only = False)
class Audio:

	source : pytags.Media
	part   : int | None = None

	def __post_init__(self):
		if self.part is not None:
			if self.part <= 0:
				raise ValueError(f'Part number less then 0 or equal: {self.part}')

	@functools.cached_property
	def info(self):
		return {
			m.groups()[0]: m.groups()[1]
			for m in re.finditer(
				r'(\w+)=(.+)',
				subprocess.run(
					args = (
						'ffprobe',
						'-v', 'quiet',
						'-select_streams', 'a:0',
						'-show_entries',
						'format=bit_rate:stream=sample_rate,channels,codec_name',
						'-'
					),
					input          = self.source.data,
					capture_output = True
				).stdout.decode()
			)
		}

	@dataclasses.dataclass(frozen = True, kw_only = False)
	class Bitrate:

		kilobits_per_second : int | float

		def __post_init__(self):
			if self.kilobits_per_second <= 0:
				raise ValueError

		@property
		def limit(self):
			match self.kilobits_per_second:
				case math.inf:
					return 'ba'
				case _:
					return f'ba[abr<{self.kilobits_per_second}]'

		def __lt__(self, another: 'Audio.Bitrate'):
			return self.kilobits_per_second < another.kilobits_per_second

		def __le__(self, another: 'Audio.Bitrate'):
			return self.kilobits_per_second <= another.kilobits_per_second

		def __gt__(self, another: 'Audio.Bitrate'):
			return self.kilobits_per_second > another.kilobits_per_second

		def __ge__(self, another: 'Audio.Bitrate'):
			return self.kilobits_per_second >= another.kilobits_per_second

		def __str__(self):
			return f'{self.kilobits_per_second}k'

	@functools.cached_property
	def bitrate(self):
		return Audio.Bitrate(int(float(self.info['bit_rate']) / 1000))

	@dataclasses.dataclass(frozen = True, kw_only = False)
	class Samplerate:

		per_second : int

		def __post_init__(self):
			if self.per_second <= 0:
				raise ValueError

		def __str__(self):
			return str(self.per_second)

	@functools.cached_property
	def samplerate(self):
		return Audio.Samplerate(int(self.info['sample_rate']))

	class Format(enum.Enum):
		# AAC  = 'aac'
		# ACT  = 'act'
		# ALAC = 'ALAC'
		# APE  = 'ape'
		# AU   = 'au'
		# AWB  = 'awb'
		# FLAC = 'flac'
		# M4A  = 'm4a'
		# M4B  = 'm4b'
		# MOGA = 'moga'
		# MOGG = 'mog'
		MP3  = 'mp3'
		# MPC  = 'mpc'
		# OGG  = 'ogg'
		# OPUS = 'opus'
		# RAW  = 'raw'
		# RF64 = 'rf64'
		# WAV  = 'wav'

	@functools.cached_property
	def format(self):
		return Audio.Format(self.info['codec_name'])

	class Channels(enum.Enum):

		mono   = '1'
		stereo = '2'

		@property
		def number(self):
			if self.name == 'mono':
				return 1
			elif self.name == 'stereo':
				return 2
			raise NotImplementedError

	@functools.cached_property
	def channels(self):
		return Audio.Channels(self.info['channels'])

	def converted(self, bitrate: Bitrate, samplerate: Samplerate, format: Format, channels: Channels):
		return dataclasses.replace(
			self,
			source = pytags.Media(
				data = subprocess.run(
					args = (
						'ffmpeg',
						'-y',
						'-hide_banner', '-loglevel', 'error',
						'-i', '-',
						'-vn', '-ar', str(samplerate), '-ac', str(channels.number), '-b:a', str(bitrate),
						'-f', format.value,
						'-'
					),
					input          = self.source.data,
					capture_output = True
				).stdout
			)
		)

	def splitted(self, parts: int):

		if parts <= 0:
			raise ValueError

		for n in range(parts):
			result = dataclasses.replace(
				self,
				source = pytags.Media(
					data = subprocess.run(
						args = (
							'ffmpeg',
							'-y',
							'-hide_banner', '-loglevel', 'error',
							'-ss', str(math.floor(self.tags.duration / parts * n)),
							'-i', '-',
							'-t', str(math.ceil(self.tags.duration / parts)),
							'-vn',
							'-ar', str(self.samplerate.per_second),
							'-ac', str(self.channels.number),
							'-b:a', f'{self.bitrate.kilobits_per_second}k',
							'-f', self.format.value,
							'-'
						),
						input          = self.source.data,
						capture_output = True
					).stdout
				),
				part = n + 1
			).tagged(
				artist = self.tags.artist,
				album  = self.tags.album,
				title  = self.tags.title
			)
			if self.tags.cover is not None:
				yield result.covered(self.tags.cover)
			else:
				yield result

	@property
	def io(self):
		return io.BytesIO(self.source.data)

	@functools.cached_property
	def tags(self):
		return pytags.Tags(self.source)

	def tagged(self, **update: str):
		return Audio(self.tags(**update).source)

	def __len__(self):
		return len(self.source.data)

	def covered(self, cover: bytes):

		stream = self.io

		mutags = mutagen.id3.ID3(stream)
		mutags.add(
			mutagen.id3.APIC(
				3,
				'image/jpeg',
				3,
				'Front cover',
				cover
			)
		)
		stream.seek(0)
		mutags.save(stream)

		return dataclasses.replace(
			self,
			source = pytags.Media(
				data = stream.getvalue()
			)
		)