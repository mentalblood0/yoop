import dataclasses
import functools
import itertools
import math
import pathlib
import subprocess
import typing

from .Url import Url
from .Media import Media


@dataclasses.dataclass(frozen=True, kw_only=False)
class Playlist:
    url: Url

    fields = (
        "playlist_id",
        "playlist_title",
        "playlist_count",
        "playlist_uploader",
        "playlist_uploader_id",
    )

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
                        *itertools.chain(
                            *(("--print", key) for key in Playlist.fields)
                        ),
                        self.url.value,
                    ),
                    capture_output=True,
                )
                .stdout.decode()
                .split("\n"),
            )
        )

    @typing.overload
    def __getitem__(self, key: int) -> typing.Union["Playlist", Media]:
        ...

    @typing.overload
    def __getitem__(
        self, key: slice
    ) -> typing.Generator[typing.Union["Playlist", Media], None, None]:
        ...

    def __getitem__(self, key: slice | int):
        if isinstance(key, slice):
            return (
                Playlist(Url(address))
                if "/playlist?" in address
                else Media(Url(address))
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
            )
        return next(
            iter(
                self[
                    key : key + int(math.copysign(1, key)) : int(math.copysign(1, key))
                ]
            )
        )

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

        @dataclasses.dataclass(frozen=True, kw_only=False)
        class Avatar:
            uploader: "Playlist.Uploader"

            @functools.cached_property
            def data(self):
                temp = pathlib.Path("avatar.jpg")

                subprocess.run(
                    args=(
                        "yt-dlp",
                        self.uploader.url,
                        "--write-thumbnail",
                        "--playlist-items",
                        "0",
                        "-o",
                        str(temp),
                    ),
                    capture_output=True,
                )

                result = temp.read_bytes()
                temp.unlink()
                return result

            def resized(self, width: int):
                if width <= 0:
                    raise ValueError

                return subprocess.run(
                    args=(
                        "ffmpeg",
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        "-",
                        "-vf",
                        f"scale={width}:-1",
                        "-f",
                        "apng",
                        "-",
                    ),
                    input=self.data,
                    capture_output=True,
                ).stdout

        @functools.cached_property
        def avatar(self):
            return Playlist.Uploader.Avatar(self)

    @functools.cached_property
    def uploader(self):
        return Playlist.Uploader(self)
