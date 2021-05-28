from typing import Dict, List
from setuptools import setup
from pathlib import Path

from cast_control import \
  __version__, __author__


NAME: str = 'cast_control'
SHORT_NAME: str = 'castctl'
LICENSE: str = 'AGPL-3.0'
PY_VERSION: str = '>=3.7'

CMD_PT: str = f'{NAME}.command:cmd'

ENTRY_POINTS: Dict[str, List[str]] = {
  'console_scripts': [
    f'{NAME} = {CMD_PT}',
    f'{SHORT_NAME} = {CMD_PT}',
  ]
}

REQS: List[str] = Path('requirements.txt') \
  .read_text() \
  .split('\n')

README: str = Path('README.md').read_text()

ASSET_DIRS: List[str] = [
  'assets/cast_control.desktop',
  'assets/icon/cc-*.png',
]

PKG_DATA: Dict[str, List[str]] = {
  NAME: ASSET_DIRS
}

PROJECT_URLS: Dict[str, str] = {
  'Homepage': 'https://alexdelorenzo.dev/'
}

setup(
  name=NAME,
  version=__version__,
  description='📺 Control Chromecasts from Linux and D-Bus',
  long_description=README,
  long_description_content_type='text/markdown',
  url='https://github.com/alexdelorenzo/cast_control',
  project_urls=PROJECT_URLS,
  author=__author__,
  license=LICENSE,
  packages=[NAME],
  zip_safe=True,
  install_requires=REQS,
  entry_points=ENTRY_POINTS,
  python_requires=PY_VERSION,
  package_data=PKG_DATA,
)
