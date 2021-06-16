from typing import List
from .types import Final


__author__: Final[str] = 'Alex DeLorenzo <alex@alexdelorenzo.dev>'
__copyright__: Final[str] = \
  f'Copyright 2021 {__author__}. Licensed under terms of the {__license__}.'
__license__: Final[str] = 'AGPL-3.0'
__version__: Final[str] = '0.10.9'

HOMEPAGE: Final[str] = "https://github.com/alexdelorenzo/cast_control"
NAME: Final[str] = 'cast_control'
SHORT_NAME: Final[str] = 'castctl'
DESCRIPTION: Final[str] = '📺 Control Chromecasts from Linux and D-Bus'

ENTRYPOINT_NAME: Final[str] = 'cli'
CLI_MODULE_NAME: Final[str] = f'{NAME}.cli'

CMD_PT: Final[str] = f'{CLI_MODULE_NAME}:{ENTRYPOINT_NAME}'

ASSET_DIRS: Final[List[str]] = [
  'assets/*.desktop',
  'assets/icon/cc-*.svg',
]
