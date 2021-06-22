from typing import Dict, List
from setuptools import setup
from pathlib import Path

from cast_control import HOMEPAGE, __license__, NAME, \
  SHORT_NAME, DESCRIPTION, __author__, PROJECT_URLS, \
  PKG_DATA, ENTRY_POINTS, PY_VERSION


REQS: List[str] = Path('requirements.txt') \
  .read_text() \
  .splitlines()

setup(
  name=NAME,
  packages=[NAME],
  install_requires=REQS,
  python_requires=PY_VERSION,
  entry_points=ENTRY_POINTS,
  package_data=PKG_DATA,
  project_urls=PROJECT_URLS,
  url=HOMEPAGE,
  description=DESCRIPTION,
  license=__license__,
)
