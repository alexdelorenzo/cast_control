from setuptools import setup
from pathlib import Path


requirements = \
  Path('requirements.txt') \
    .read_text() \
    .split('\n')
readme = Path('README.md').read_text()

setup(
      name="chromecast_mpris",
      version="0.1.2",
      description="Control Chromecasts via MPRIS.",
      long_description=readme,
      long_description_content_type="text/markdown",
      url="https://alexdelorenzo.dev",
      author="Alex DeLorenzo",
      license="AGPL-3.0",
      packages=['chromecast_mpris'],
      zip_safe=True,
      install_requires=requirements,
      entry_points={"console_scripts":
                      ["chromecast_mpris = chromecast_mpris.command:cmd"]},
      python_requires='>=3.6',
)
