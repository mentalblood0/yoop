import typing
import pydantic
import functools
import subprocess

from .Link  import Link



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Playlist:

	link : Link

	@typing.overload
	def __getitem__(self, key: int) -> Link:
		...
	@typing.overload
	def __getitem__(self, key: slice) -> typing.Generator[Link, None, None]:
		...
	@typing.overload
	def __getitem__(self, key: str) -> str:
		...
	@pydantic.validate_call(config = {'arbitrary_types_allowed': True})
	def __getitem__(self, key: slice | int | str):
		match key:
			case slice():
				return (
					Link(address)
					for address in subprocess.run(
						args = (
							'yt-dlp',
							'--flat-playlist',
							'--print', 'url',
							'--playlist-items', f'{key.start or ""}:{key.stop or ""}:{key.step}',
							self.link.value
						),
						capture_output = True
					).stdout.decode().splitlines()
				)
			case int():
				return next(iter(self[key : key + 1 : 1]))
			case str():
				return subprocess.run(
					args = (
						'yt-dlp',
						'--flat-playlist',
						'--print', key,
						'--playlist-items', '1',
						self.link.value
					),
					capture_output = True
				).stdout.decode().rstrip()

	@functools.cached_property
	def __iter__(self):
		return self[::1]

	@functools.cached_property
	def title(self):
		return self['playlist_title']

	@functools.cached_property
	def uploader(self):
		return self['playlist_uploader']