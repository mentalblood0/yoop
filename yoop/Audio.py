import dataclasses
import enum
import functools
import io
import math
import re
import subprocess


@dataclasses.dataclass(frozen=True, kw_only=False)
class Audio:
    data: bytes
    verified: bool = True

    def __post_init__(self):
        if not self.data:
            raise ValueError("No data provided (empty bytes object)")

        if self.verified:
            errors = subprocess.run(
                args=("ffmpeg", "-v", "error", "-i", "-", "-f", "null", "-"),
                input=self.data,
                capture_output=True,
            ).stderr.decode()
            if errors:
                raise ValueError(f"ffmpeg have errors checking data: {errors}")

    @functools.cached_property
    def info(self):
        return {
            m.groups()[0]: m.groups()[1]
            for m in re.finditer(
                r"(\w+)=(.+)",
                subprocess.run(
                    args=(
                        "ffprobe",
                        "-v",
                        "quiet",
                        "-select_streams",
                        "a:0",
                        "-show_entries",
                        "format=bit_rate:stream=sample_rate,channels,codec_name",
                        "-",
                    ),
                    input=self.data,
                    capture_output=True,
                ).stdout.decode(),
            )
        }

    @dataclasses.dataclass(frozen=True, kw_only=False)
    class Bitrate:
        kilobits_per_second: int | float

        def __post_init__(self):
            if self.kilobits_per_second <= 0:
                raise ValueError

        @property
        def limit(self):
            if self.kilobits_per_second == math.inf:
                return "ba"
            return f"ba[abr<{self.kilobits_per_second}]"

        def __lt__(self, another: "Audio.Bitrate"):
            return self.kilobits_per_second < another.kilobits_per_second

        def __le__(self, another: "Audio.Bitrate"):
            return self.kilobits_per_second <= another.kilobits_per_second

        def __gt__(self, another: "Audio.Bitrate"):
            return self.kilobits_per_second > another.kilobits_per_second

        def __ge__(self, another: "Audio.Bitrate"):
            return self.kilobits_per_second >= another.kilobits_per_second

        def __str__(self):
            return f"{self.kilobits_per_second}k"

    @functools.cached_property
    def bitrate(self):
        return Audio.Bitrate(int(float(self.info["bit_rate"]) / 1000))

    @dataclasses.dataclass(frozen=True, kw_only=False)
    class Samplerate:
        per_second: int

        def __post_init__(self):
            if self.per_second <= 0:
                raise ValueError

        def __str__(self):
            return str(self.per_second)

    @functools.cached_property
    def samplerate(self):
        return Audio.Samplerate(int(self.info["sample_rate"]))

    class Format(enum.Enum):
        # AAC  = 'aac'
        # ACT  = 'act'
        # ALAC = 'ALAC'
        # APE  = 'ape'
        # AU   = 'au'
        # AWB  = 'awb'
        # FLAC = 'flac'
        # M4A  = 'm4a'
        # M4B  = 'm4b'
        # MOGA = 'moga'
        # MOGG = 'mog'
        MP3 = "mp3"
        # MPC  = 'mpc'
        # OGG  = 'ogg'
        # OPUS = 'opus'
        # RAW  = 'raw'
        # RF64 = 'rf64'
        # WAV  = 'wav'

    @functools.cached_property
    def format(self):
        return Audio.Format(self.info["codec_name"])

    class Channels(enum.Enum):
        mono = "1"
        stereo = "2"

        @property
        def number(self):
            if self.name == "mono":
                return 1
            elif self.name == "stereo":
                return 2
            raise NotImplementedError

    @functools.cached_property
    def channels(self):
        return Audio.Channels(self.info["channels"])

    def converted(
        self,
        bitrate: Bitrate,
        samplerate: Samplerate,
        format: Format,
        channels: Channels,
        verified: bool = True,
    ):
        return Audio(
            data=subprocess.run(
                args=(
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    "-",
                    "-vn",
                    "-ar",
                    str(samplerate),
                    "-ac",
                    str(channels.number),
                    "-b:a",
                    str(bitrate),
                    "-f",
                    format.value,
                    "-",
                ),
                input=self.data,
                capture_output=True,
            ).stdout,
            verified=verified,
        )

    def splitted(self, parts: int, verified: bool = True):
        if parts <= 0:
            raise ValueError
        return (
            Audio(
                data=subprocess.run(
                    args=(
                        "ffmpeg",
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-ss",
                        str(math.floor(self.duration / parts * n)),
                        "-i",
                        "-",
                        "-t",
                        str(math.ceil(self.duration / parts)),
                        "-vn",
                        "-ar",
                        str(self.samplerate.per_second),
                        "-ac",
                        str(self.channels.number),
                        "-b:a",
                        f"{self.bitrate.kilobits_per_second}k",
                        "-f",
                        self.format.value,
                        "-",
                    ),
                    input=self.data,
                    capture_output=True,
                ).stdout,
                verified=verified,
            )
            for n in range(parts)
        )

    @functools.cached_property
    def duration(self):
        hours, minutes, seconds = re.findall(
            r"time=(\d+):(\d+):(\d+\.\d+)",
            subprocess.run(
                args=("ffmpeg", "-i", "-", "-f", "null", "-"),
                input=self.data,
                capture_output=True,
            ).stderr.decode(),
        )[-1]
        return (int(hours) * 60 + int(minutes)) * 60 + float(seconds)

    @property
    def io(self):
        return io.BytesIO(self.data)

    def __len__(self):
        return len(self.data)
