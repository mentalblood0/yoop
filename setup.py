import pathlib
import setuptools



if __name__ == '__main__':

	setuptools.setup(
		name                          = 'yoop',
		version                       = '0.3.0',
		description                   = 'Object-oriented library based on yt-dlp',
		long_description              = (pathlib.Path(__file__).parent / 'README.md').read_text(),
		long_description_content_type = 'text/markdown',
		author                        = 'mentalblood',
		packages                      = setuptools.find_packages(exclude = ['tests*']),
		install_requires              = [
			'mutagen'
		]
	)