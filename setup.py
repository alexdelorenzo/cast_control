from __future__ import annotations
from typing import Final
from setuptools import setup, find_packages
from pathlib import Path

from cast_control import HOMEPAGE, NAME, \
  DESCRIPTION, PROJECT_URLS, PKG_DATA, ENTRY_POINTS, \
  PY_VERSION, PKGS, __license__


REQS: Final[list[str]] = Path('requirements.txt') \
  .read_text() \
  .splitlines()

ALL_PKGS: Final[list[str]] = list({
  *PKGS,
  *find_packages(),
})

setup(
  name=NAME,
  packages=ALL_PKGS,
  install_requires=REQS,
  python_requires=PY_VERSION,
  entry_points=ENTRY_POINTS,
  package_data=PKG_DATA,
  project_urls=PROJECT_URLS,
  url=HOMEPAGE,
  description=DESCRIPTION,
  license=__license__,
)
