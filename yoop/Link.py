import pydantic



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Link:

	value : pydantic.HttpUrl

	@property
	def string(self):
		return str(self.value)