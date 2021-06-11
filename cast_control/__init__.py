__version__ = '0.10.8'
__author__ = 'Alex DeLorenzo <alex@alexdelorenzo.dev>'
from typing import List


HOMEPAGE: str = "https://github.com/alexdelorenzo/cast_control"
LICENSE: str = 'AGPL-3.0'
NAME: str = 'cast_control'
SHORT_NAME: str = 'castctl'
DESCRIPTION: str = '📺 Control Chromecasts from Linux and D-Bus'

ENTRYPOINT_NAME: str = 'cli'
CLI_MODULE_NAME: str = f'{NAME}.cli'

CMD_PT: str = f'{CLI_MODULE_NAME}:{ENTRYPOINT_NAME}'

ASSET_DIRS: List[str] = [
  'assets/*.desktop',
  'assets/icon/cc-*.png',
]
