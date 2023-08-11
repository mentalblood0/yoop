import enum
import pydantic
import datetime
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
	def data(self):
		return subprocess.run(
			args = (
				'yt-dlp',
				'-o', '-',
				self.link.value
			),
			capture_output = True
		).stdout

	@functools.cached_property
	def id(self):
		return self['id']

	@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
	class Title:
		simple      : str
		full        : str
		alternative : str

	@functools.cached_property
	def title(self):
		return Video.Title(
			simple      = self['title'],
			full        = self['fulltitle'],
			alternative = self['alt_title']
		)

	@functools.cached_property
	def extension(self):
		return self['ext']

	@functools.cached_property
	def channel(self):
		return self['channel']

	@functools.cached_property
	def uploader(self):
		return self['uploader']

	@functools.cached_property
	def creator(self):
		return self['creator']

	@functools.cached_property
	def description(self):
		return self['description']

	@functools.cached_property
	def uploaded(self):
		return datetime.datetime.fromtimestamp(int(self['timestamp']))

	@functools.cached_property
	def released(self):
		return datetime.datetime.fromtimestamp(int(self['release_timestamp']))

	@functools.cached_property
	def modified(self):
		return datetime.datetime.fromtimestamp(int(self['modified_timestamp']))

	@functools.cached_property
	def license(self):
		return self['license']

	@functools.cached_property
	def location(self):
		return self['location']

	@functools.cached_property
	def duration(self):
		return datetime.timedelta(seconds = int(self['duration']))

	@functools.cached_property
	def viewed(self):
		return int(self['views'])

	@functools.cached_property
	def viewing(self):
		return int(self['concurrent_view_count'])

	@functools.cached_property
	def likes(self):
		return int(self['like_count'])

	@functools.cached_property
	def dislikes(self):
		return int(self['dislike_count'])

	@functools.cached_property
	def reposts(self):
		return int(self['repost_count'])

	@functools.cached_property
	def rating(self):
		return float(self['average_rating'])

	@functools.cached_property
	def age(self):
		return int(self['age_limit'])

	class Liveness(enum.Enum):
		will  = 'is_upcoming'
		alive = 'is_live'
		dying = 'post_live'
		was   = 'was_live'
		no    = 'not_live'

	@functools.cached_property
	def liveness(self):
		return Video.Liveness(self['live_status'])

	@functools.cached_property
	def live(self):
		return bool(self['is_live'])

	@functools.cached_property
	def lived(self):
		return bool(self['was_live'])

	class Availability(enum.Enum):
		private       = 'private'
		premium       = 'premium_only'
		subscriber    = 'subscriber_only'
		authenticated = 'needs_auth'
		unlisted      = 'unlisted'
		public        = 'public'

	@functools.cached_property
	def availability(self):
		return Video.Availability(self['availability'])