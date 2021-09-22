from __future__ import annotations

from .types import Final


# module metadata
__author__: Final[str] = 'Alex DeLorenzo <alex@alexdelorenzo.dev>'
__license__: Final[str] = 'AGPL-3.0'
__copyright__: Final[str] = \
  f'Copyright 2021 {__author__}. Licensed under terms of the {__license__}.'
__version__: Final[str] = '0.11.4.post1'

NAME: Final[str] = 'cast_control'
SHORT_NAME: Final[str] = 'castctl'
DESCRIPTION: Final[str] = '📺 Control Chromecasts from Linux and D-Bus'
HOMEPAGE: Final[str] = "https://github.com/alexdelorenzo/cast_control"
TITLE: Final[str] = 'Cast Control'

ENTRYPOINT_NAME: Final[str] = 'cli'
CLI_MODULE_NAME: Final[str] = f'{NAME}.app.cli'


# packaging metadata
CMD_PT: Final[str] = f'{CLI_MODULE_NAME}:{ENTRYPOINT_NAME}'
PY_VERSION: Final[str] = '>=3.7'
PKGS: Final[list[str]] = [
  NAME,
  f'{NAME}.app',
  f'{NAME}.device',
]

PROJECT_URLS: Final[dict[str, str]] = {
  'Homepage': 'https://alexdelorenzo.dev/',
  'Source': HOMEPAGE
}

ASSET_DIRS: Final[list[str]] = [
  'assets/*.desktop',
  'assets/icon/cc-*.svg',
  'assets/icon/*.yml',
]

CONSOLE_SCRIPTS: Final[list[str]] = [
  f'{NAME} = {CMD_PT}',
  f'{SHORT_NAME} = {CMD_PT}',
]

PKG_DATA: Final[dict[str, list[str]]] = {
  NAME: ASSET_DIRS
}

ENTRY_POINTS: Final[dict[str, list[str]]] = {
  'console_scripts': CONSOLE_SCRIPTS
}
