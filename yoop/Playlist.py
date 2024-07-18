import base64
import dataclasses
import functools
import itertools
import math
import re
import subprocess

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
            if "watch?v=" in url.value:
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
                if not (("bandcamp.com" in self.url.value) and address.endswith(".mp4"))
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
            return [
                self.content(self.url / a)
                for a in re.findall(r"\"(\/(?:album|track)\/[^\"]+)\"", page)
                + re.findall(r";(\/(?:album|track)\/[^&\"]+)(?:&|\")", page)
            ]
        return [
            self.content(Url(address))
            for address in subprocess.run(
                args=("yt-dlp", "--flat-playlist", "--print", "url", self.url.value), capture_output=True
            )
            .stdout.decode()
            .splitlines()
        ]

    def __iter__(self):
        return self[::1]

    @functools.cached_property
    def available(self):
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
    def length(self):
        return int(self.info["playlist_count"])

    def __len__(self):
        return self.length

    @dataclasses.dataclass(frozen=True, kw_only=False)
    class Uploader:
        playlist: "Playlist"

        @functools.cached_property
        def name(self):
            return self.playlist.info["playlist_uploader"]

        @functools.cached_property
        def id(self):
            return self.playlist.info["playlist_uploader_id"]

        @functools.cached_property
        def url(self):
            return f"https://www.youtube.com/{self.id}"
