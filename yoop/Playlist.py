import base64
import dataclasses
import functools
import itertools
import math
import re
import subprocess
from typing import Generator, Union, overload

from .Media import Media
from .Url import Url


@dataclasses.dataclass(frozen=True, kw_only=False)
class Playlist:
    url: Url

    fields = ("playlist_id", "playlist_title", "playlist_count", "playlist_uploader", "playlist_uploader_id")

    @staticmethod
    def content(url: Url):
        if "bandcamp.com" in url.value:
            if "/track/" in url.value:
                return Media(url)
            return Playlist(url)
        elif "youtube.com" in url.value:
            if ("watch?v=" in url.value) or ("/shorts/" in url.value):
                return Media(url)
            return Playlist(url)
        raise ValueError

    @functools.cached_property
    def info(self):
        return dict(
            zip(
                Playlist.fields,
                subprocess.run(
                    args=(
                        "yt-dlp",
                        "--skip-download",
                        "--playlist-items",
                        "1",
                        *itertools.chain(*(("--print", key) for key in Playlist.fields)),
                        self.url.value,
                    ),
                    capture_output=True,
                )
                .stdout.decode()
                .split("\n"),
            )
        )

    @overload
    def __getitem__(self, key: slice) -> Generator[Union[Media, "Playlist"], None, None]: ...

    @overload
    def __getitem__(self, key: int) -> Union[Media, "Playlist"]: ...

    def __getitem__(self, key: slice | int):
        if (
            ("bandcamp.com" in self.url.value)
            and ("/track/" not in self.url.value)
            and ("/album/" not in self.url.value)
        ):
            if isinstance(key, slice):
                return (i for i in self.items[key])
            return self.items[key]
        if isinstance(key, slice):
            return (
                self.content(Url(address))
                for address in subprocess.run(
                    args=(
                        "yt-dlp",
                        "--flat-playlist",
                        "--print",
                        "url",
                        "--playlist-items",
                        f'{key.start or ""}:{key.stop or ""}:{key.step}',
                        self.url.value,
                    ),
                    capture_output=True,
                )
                .stdout.decode()
                .splitlines()
                if (not (("bandcamp.com" in self.url.value) and address.endswith(".mp4"))) and (not address == "NA")
            )
        try:
            return next(iter(self[key : key + int(math.copysign(1, key)) : int(math.copysign(1, key))]))
        except StopIteration:
            raise IndexError

    @functools.cached_property
    def items(self):
        if (
            ("bandcamp.com" in self.url.value)
            and ("/track/" not in self.url.value)
            and ("/album/" not in self.url.value)
        ):
            page = base64.b64decode(
                re.findall(
                    r"Dumping request.*\n(.*)\n",
                    subprocess.run(
                        args=(
                            "yt-dlp",
                            "--flat-playlist",
                            "--skip-download",
                            "--dump-pages",
                            (self.url / "music").value,
                        ),
                        capture_output=True,
                    ).stdout.decode(),
                )[0]
            ).decode()
            result = [
                self.content(self.url / a) if "http" not in a else self.content(Url(a))
                for a in re.findall(r'href="([^&\n]+)&amp;tab=music', page)
                + re.findall(r"\"(\/(?:album|track)\/[^\"]+)\"", page)
                + re.findall(r";(\/(?:album|track)\/[^&\"]+)(?:&|\")", page)
            ]
            for a in re.findall(r"page_url&quot;:&quot;([^&]+)&", page):
                c = self.content(Url(a) if "http" in a else self.url / a)
                if c not in result:
                    result.append(c)
            return result

        return [
            self.content(Url(address))
            for address in subprocess.run(
                args=("yt-dlp", "--flat-playlist", "--print", "url", self.url.value), capture_output=True
            )
            .stdout.decode()
            .splitlines()
            if address != "NA"
        ]

    def __iter__(self):
        return self[::1]

    @functools.cached_property
    def available(self):
        if "bandcamp.com" in self.url.value:
            return True
        try:
            self.title
        except KeyError:
            return False
        return True

    @functools.cached_property
    def id(self):
        return self.info["playlist_id"]

    @functools.cached_property
    def title(self):
        return self.info["playlist_title"]

    @functools.cached_property
    def uploader(self):
        if "playlist_uploader" not in self.info:
            return "NA"
        return self.info["playlist_uploader"]

    @functools.cached_property
    def length(self):
        try:
            return int(self.info["playlist_count"])
        except ValueError:
            return 0

    def __len__(self):
        return self.length
