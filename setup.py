__author__ = "Alex DeLorenzo"
from setuptools import setup
from pathlib import Path


NAME = "chromecast_mpris"
VERSION = "0.3.0"
LICENSE = "AGPL-3.0"

requirements = \
  Path('requirements.txt') \
    .read_text() \
    .split('\n')

readme = Path('README.md').read_text()

setup(
      name=NAME,
      version=VERSION,
      description="📺 Control Chromecasts from Linux and D-Bus",
      long_description=readme,
      long_description_content_type="text/markdown",
      url="https://alexdelorenzo.dev",
      author=__author__,
      license=LICENSE,
      packages=[NAME],
      zip_safe=True,
      install_requires=requirements,
      entry_points={"console_scripts":
                      [f"{NAME} = {NAME}.command:cmd"]},
      python_requires='>=3.6',
)
