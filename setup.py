from typing import Dict, List
from setuptools import setup
from pathlib import Path

from cast_control import HOMEPAGE, __license__, NAME, \
  SHORT_NAME, DESCRIPTION, __version__, __author__, \
  ENTRYPOINT_NAME, CMD_PT, ASSET_DIRS


PY_VERSION: str = '>=3.7'

ENTRY_POINTS: Dict[str, List[str]] = {
  'console_scripts': [
    f'{NAME} = {CMD_PT}',
    f'{SHORT_NAME} = {CMD_PT}',
  ]
}

REQS: List[str] = Path('requirements.txt') \
  .read_text() \
  .splitlines()

README: str = Path('README.md').read_text()
CONTENT_TYPE: str = 'text/markdown'

PKG_DATA: Dict[str, List[str]] = {
  NAME: ASSET_DIRS
}

PROJECT_URLS: Dict[str, str] = {
  'Homepage': 'https://alexdelorenzo.dev/',
  'Source': HOMEPAGE
}

setup(
  name=NAME,
  version=__version__,
  description=DESCRIPTION,
  long_description=README,
  long_description_content_type=CONTENT_TYPE,
  url=HOMEPAGE,
  project_urls=PROJECT_URLS,
  author=__author__,
  license=__license__,
  packages=[NAME],
  zip_safe=True,
  install_requires=REQS,
  entry_points=ENTRY_POINTS,
  python_requires=PY_VERSION,
  package_data=PKG_DATA,
)
