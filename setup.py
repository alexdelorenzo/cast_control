__author__ = "Alex DeLorenzo"
from setuptools import setup
from pathlib import Path


NAME = "chromecast_mpris"
VERSION = "0.4.0"
LICENSE = "AGPL-3.0"

# potential new name
NEW_NAME = "cast_control"

ENTRY_POINTS = {
  "console_scripts": [
    f"{NAME} = {NAME}.command:cmd",
    f"{NEW_NAME} = {NAME}.command:cmd"
  ]
}

REQS = Path('requirements.txt') \
  .read_text() \
  .split('\n')

README = Path('README.md').read_text()


setup(
  name=NAME,
  version=VERSION,
  description="📺 Control Chromecasts from Linux and D-Bus",
  long_description=README,
  long_description_content_type="text/markdown",
  url="https://alexdelorenzo.dev",
  author=__author__,
  license=LICENSE,
  packages=[NAME],
  zip_safe=True,
  install_requires=REQS,
  entry_points=ENTRY_POINTS,
  python_requires='>=3.6',
)
