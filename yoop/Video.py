import enum
import typing
import pydantic
import datetime
import functools
import itertools
import subprocess

from .Link import Link



@pydantic.dataclasses.dataclass(frozen = False, kw_only = False)
class Video:

	link  : typing.Final[Link]

	fields = (
		'age_limit',
		'alt_title',
		'availability',
		'average_rating',
		'channel',
		'concurrent_view_count',
		'dislike_count',
		'duration',
		'ext',
		'fulltitle',
		'id',
		'is_live',
		'license',
		'like_count',
		'live_status',
		'location',
		'modified_timestamp',
		'release_timestamp',
		'repost_count',
		'timestamp',
		'title',
		'uploader',
		'views',
		'was_live',
		'creator',
		'description'
	)

	@property
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
	def info(self):
		return dict(
			zip(
				Video.fields,
				subprocess.run(
					args = (
						'yt-dlp',
						'--skip-download',
						*itertools.chain(
							*(
								('--print', key)
								for key in Video.fields
							)
						),
						self.link.value
					),
					capture_output = True
				).stdout.decode().split('\n')
			)
		)

	@property
	def id(self):
		return self.info['id']

	@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
	class Title:
		simple      : str
		full        : str
		alternative : str

	@property
	def title(self):
		return Video.Title(
			simple      = self.info['title'],
			full        = self.info['fulltitle'],
			alternative = self.info['alt_title']
		)

	@property
	def extension(self):
		return self.info['ext']

	@property
	def channel(self):
		return self.info['channel']

	@property
	def uploader(self):
		return self.info['uploader']

	@property
	def creator(self):
		return self.info['creator']

	@property
	def description(self):
		return self.info['description']

	@property
	def uploaded(self):
		return datetime.datetime.fromtimestamp(int(self.info['timestamp']))

	@property
	def released(self):
		return datetime.datetime.fromtimestamp(int(self.info['release_timestamp']))

	@property
	def modified(self):
		return datetime.datetime.fromtimestamp(int(self.info['modified_timestamp']))

	@property
	def license(self):
		return self.info['license']

	@property
	def location(self):
		return self.info['location']

	@property
	def duration(self):
		return datetime.timedelta(seconds = int(self.info['duration']))

	@property
	def viewed(self):
		return int(self.info['views'])

	@property
	def viewing(self):
		return int(self.info['concurrent_view_count'])

	@property
	def likes(self):
		return int(self.info['like_count'])

	@property
	def dislikes(self):
		return int(self.info['dislike_count'])

	@property
	def reposts(self):
		return int(self.info['repost_count'])

	@property
	def rating(self):
		return float(self.info['average_rating'])

	@property
	def age(self):
		return int(self.info['age_limit'])

	class Liveness(enum.Enum):
		will  = 'is_upcoming'
		alive = 'is_live'
		dying = 'post_live'
		was   = 'was_live'
		no    = 'not_live'

	@property
	def liveness(self):
		return Video.Liveness(self.info['live_status'])

	@property
	def live(self):
		return self.info['is_live'] == 'True'

	@property
	def lived(self):
		return self.info['was_live'] == 'True'

	class Availability(enum.Enum):
		private       = 'private'
		premium       = 'premium_only'
		subscriber    = 'subscriber_only'
		authenticated = 'needs_auth'
		unlisted      = 'unlisted'
		public        = 'public'

	@property
	def availability(self):
		return Video.Availability(self.info['availability'])