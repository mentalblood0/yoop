import re
import datetime
import functools
import subprocess
import dataclasses



@dataclasses.dataclass(frozen = True, kw_only = False)
class Tags:

	data : bytes

	def __getitem__(self, key: str):
		try:
			return str(
				next(
					re.finditer(
						f'TAG:{key}=(.+)',
						subprocess.run(
							args = (
								'ffprobe',
								'-v', 'quiet',
								'-show_entries',
								f'format_tags={key}',
								'-'
							),
							input          = self.data,
							capture_output = True
						).stdout.decode()
					)
				).groups()[0]
			)
		except IndexError as exception:
			raise KeyError from exception

	@functools.cached_property
	def artist(self):
		return self['artist']

	@functools.cached_property
	def album(self):
		return self['album']

	@functools.cached_property
	def title(self):
		return self['title']

	@functools.cached_property
	def date(self):
		return datetime.datetime.fromisoformat(self['date'])

	@functools.cached_property
	def cover(self):
		return subprocess.run(
			args = (
				'ffmpeg',
				'-v', 'quiet',
				'-i', '-',
				'-an', '-vcodec', 'copy',
				'-f', 'mjpeg',
				'-'
			),
			input          = self.data,
			capture_output = True
		).stdout or None