import pytest
import functools

from .. import yoop



@pytest.fixture
@functools.cache
def channel():
	return yoop.Playlist(
		yoop.Url(
			'https://www.youtube.com/@KaneB'
		)
	)

@pytest.mark.parametrize(
	'field',
	(
		'id',
		'title',
		'uploader'
	)
)
def test_string_fields(channel: yoop.Playlist, field: str):
	assert isinstance(channel.__getattribute__(field), str)
	assert len(channel.__getattribute__(field))