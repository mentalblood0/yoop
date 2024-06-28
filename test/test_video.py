import functools

import pytest

from .. import yoop
from .test_channel import channel


@functools.lru_cache
def video():
    result = channel()[0]
    if isinstance(result, yoop.Media):
        return result
    raise ValueError


@pytest.mark.parametrize(
    "field",
    (
        "id",
        "extension",
        "channel",
        "uploader",
        "creator",
        "description",
        "license",
        "location",
    ),
)
def test_string_fields(field: str):
    value = getattr(video(), field)
    assert isinstance(value, str)
    assert len(value)


@pytest.mark.skip(reason="expensive in terms of traffic and time")
def test_data():
    assert len(video().data)
