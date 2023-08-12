import typing
import pydantic
import functools
import itertools
import subprocess

from .Video import Video



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Playlist:

	link : pydantic.HttpUrl

	fields = (
		'playlist_id',
		'playlist_title',
		'playlist_count',
		'playlist_uploader'
	)

	@functools.cached_property
	def info(self):
		return dict(
			zip(
				Playlist.fields,
				subprocess.run(
					args = (
						'yt-dlp',
						'--skip-download',
						'--playlist-items', '1',
						*itertools.chain(
							*(
								('--print', key)
								for key in Playlist.fields
							)
						),
						str(self.link)
					),
					capture_output = True
				).stdout.decode().split('\n')
			)
		)

	@typing.overload
	def __getitem__(self, key: int) -> Video:
		...
	@typing.overload
	def __getitem__(self, key: slice) -> typing.Generator[Video, None, None]:
		...
	@pydantic.validate_call(config = {'arbitrary_types_allowed': True})
	def __getitem__(self, key: slice | int):
		match key:
			case slice():
				return (
					Video(pydantic.HttpUrl(address))
					for address in subprocess.run(
						args = (
							'yt-dlp',
							'--flat-playlist',
							'--print', 'url',
							'--playlist-items', f'{key.start or ""}:{key.stop or ""}:{key.step}',
							str(self.link)
						),
						capture_output = True
					).stdout.decode().splitlines()
				)
			case int():
				return next(iter(self[key : key + 1 : 1]))

	@functools.cached_property
	def __iter__(self):
		return self[::1]

	@functools.cached_property
	def id(self):
		return self.info['playlist_id']

	@functools.cached_property
	def title(self):
		return self.info['playlist_title']

	@functools.cached_property
	def __len__(self):
		return int(self.info['playlist_count'])

	@functools.cached_property
	def uploader(self):
		return self.info['playlist_uploader']