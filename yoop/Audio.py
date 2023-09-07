import re
import io
import math
import enum
import functools
import subprocess
import dataclasses
import mutagen.mp3
import mutagen.id3
import mutagen.easyid3


@dataclasses.dataclass(frozen = True, kw_only = False)
class Audio:

	data : bytes
	part : int | None = None

	class UnavailableError(Exception):
		pass

	def __post_init__(self):

		if not self.data:
			raise Audio.UnavailableError('No audio data provided (empty bytes object)')

		if (
			errors := subprocess.run(
				args = (
					'ffmpeg',
					'-v', 'error',
					'-i', '-'
					'-f', 'null',
					'-'
				),
				input          = self.data,
				capture_output = True
			).stdout.decode()
		):
			raise Audio.UnavailableError(f'ffmpeg have errors checking audio data: {errors}')

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
						'-show_entries',
						'format=duration,bit_rate:stream=sample_rate,channels,codec_name',
						'-'
					),
					input          = self.data,
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
				input          = self.data,
				capture_output = True
			).stdout
		)

	def splitted(self, parts: int):

		if self.format != Audio.Format.MP3:
			raise NotImplementedError

		if parts <= 0:
			raise ValueError

		for n in range(parts):
			result = dataclasses.replace(
				self,
				data = subprocess.run(
					args = (
						'ffmpeg',
						'-y',
						'-hide_banner', '-loglevel', 'error',
						'-ss', str(math.floor(self.duration / parts * n)),
						'-i', '-',
						'-t', str(math.ceil(self.duration / parts)),
						'-vn',
						'-ar', str(self.samplerate.per_second),
						'-ac', str(self.channels.number),
						'-b:a', f'{self.bitrate.kilobits_per_second}k',
						'-f', self.format.value,
						'-'
					),
					input          = self.data,
					capture_output = True
				).stdout,
				part = n + 1
			).tagged(
				**self.tags
			)
			if self.isCovered:
				yield result.covered(self.cover)
			else:
				yield result

	@property
	def io(self):
		return io.BytesIO(self.data)

	@functools.cached_property
	def duration(self):
		return mutagen.mp3.MP3(self.io).info.length

	@functools.cached_property
	def isCovered(self) -> bool:
		return len(mutagen.id3.ID3(self.io).getall('APIC'))

	@functools.cached_property
	def cover(self) -> bytes:
		return mutagen.id3.ID3(self.io).getall('APIC')[0].data

	@functools.cached_property
	def tags(self) -> dict[str, str]:
		return {
			i[0]: i[1]
			for i in mutagen.easyid3.EasyID3(self.io).items()
		}

	def __len__(self):
		return len(self.data)

	def tagged(self, **update: str | list[str]):

		data_io = self.io
		tags    = mutagen.easyid3.EasyID3(data_io)

		tags.update(update)
		tags.save(data_io)

		return dataclasses.replace(self, data = data_io.getvalue())

	def covered(self, cover: bytes):

		stream = self.io

		tags = mutagen.id3.ID3(stream)
		tags.add(
			mutagen.id3.APIC(
				3,
				'image/jpeg',
				3,
				'Front cover',
				cover
			)
		)
		stream.seek(0)
		tags.save(stream)

		return dataclasses.replace(self, data = stream.getvalue())