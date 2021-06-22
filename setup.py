from __future__ import annotations
from setuptools import setup
from pathlib import Path

from cast_control import Final, HOMEPAGE, NAME, \
  DESCRIPTION, PROJECT_URLS, PKG_DATA, ENTRY_POINTS, \
  PY_VERSION, PKGS, __license__


REQS: Final[list[str]] = Path('requirements.txt') \
  .read_text() \
  .splitlines()

setup(
  name=NAME,
  packages=PKGS,
  install_requires=REQS,
  python_requires=PY_VERSION,
  entry_points=ENTRY_POINTS,
  package_data=PKG_DATA,
  project_urls=PROJECT_URLS,
  url=HOMEPAGE,
  description=DESCRIPTION,
  license=__license__,
)
