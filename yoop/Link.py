import pydantic



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Link:

	value : str