import io
import math
import functools
import subprocess
import dataclasses
import mutagen.mp3
import mutagen.id3
import mutagen.easyid3



@dataclasses.dataclass(frozen = True, kw_only = False)
class PartNumber:

	current : int
	total   : int


@dataclasses.dataclass(frozen = True, kw_only = False)
class Audio:

	data : bytes
	part : PartNumber | None = None

	class UnavailableError(Exception):
		pass

	def __post_init__(self):
		if not self.data:
			raise Audio.UnavailableError from ValueError

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

	@property
	def converted(self):
		return dataclasses.replace(
			self,
			data = subprocess.run(
				args = (
					'ffmpeg',
					'-y',
					'-hide_banner', '-loglevel', 'error',
					'-i', '-',
					'-vn', '-ar', '32000', '-ac', '1', '-b:a', '96k',
					'-f', 'mp3',
					'-'
				),
				input          = self.data,
				capture_output = True
			).stdout
		)

	def splitted(self, parts: int):
		if parts <= 0:
			raise ValueError
		return (
			dataclasses.replace(
				self,
				data = subprocess.run(
					args = (
						'ffmpeg',
						'-y',
						'-hide_banner', '-loglevel', 'error',
						'-ss', str(math.floor(self.duration / parts * n)),
						'-i', '-',
						'-t', str(math.ceil(self.duration / parts)),
						'-vn', '-ar', '32000', '-ac', '1', '-b:a', '96k',
						'-f', 'mp3',
						'-'
					),
					input          = self.data,
					capture_output = True
				).stdout,
				part = PartNumber(n + 1, parts)
			).tagged
			for n in range(parts)
		)

	@property
	def io(self):
		return io.BytesIO(self.data)

	@functools.cached_property
	def duration(self):
		return mutagen.mp3.MP3(self.io).info.length

	@functools.cached_property
	def cover(self) -> bytes:
		return mutagen.id3.ID3(self.io).getall('APIC')[0].data

	@functools.cached_property
	def tags(self):
		return mutagen.easyid3.EasyID3(self.io)

	def __len__(self):
		return len(self.data)

	def tagged(self, **update: str):

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
		tags.save(stream)

		return dataclasses.replace(self, data = stream.getvalue())