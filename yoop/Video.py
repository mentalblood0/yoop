import pydantic
import functools
import subprocess

from .Link import Link



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Video:

	link : Link

	@pydantic.validate_call
	def __getitem__(self, key: str):
		return subprocess.run(
			args = (
				'yt-dlp',
				'--flat-playlist',
				'--print', key,
				self.link.value
			),
			capture_output = True
		).stdout.decode().rstrip()

	@functools.cached_property
	def title(self):
		return self['title']

	@functools.cached_property
	def channel(self):
		return self['channel']