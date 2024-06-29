import os
import pathlib

import setuptools

if __name__ == "__main__":
    if os.system("ffmpeg -version"):
        raise LookupError(
            "yoop is ffmpeg interface, so it needs ffmpeg utility in order to work. "
            "You can install it from here: https://ffmpeg.org/"
        )
    setuptools.setup(
        name="yoop",
        version="0.5.0",
        description="Object-oriented library based on yt-dlp",
        long_description=(pathlib.Path(__file__).parent / "README.md").read_text(),
        long_description_content_type="text/markdown",
        author="mentalblood",
        packages=setuptools.find_packages(exclude=["tests*"]),
        install_requires=[],
    )
