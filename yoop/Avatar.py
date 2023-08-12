import re
import json
import requests
import pydantic
import functools

from .Loggable import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Avatar(Loggable):

	channel : str

	@functools.cached_property
	def link(self):
		return max(
			json.loads(
				re.findall(
					r'"avatar":{.*"thumbnails":(\[[^]]*])',
					requests.get(self.channel).text
				)[0]
			),
			key = lambda e: e['width']
		)['url']

	@functools.cached_property
	def data(self):
		return requests.get(self.link).content