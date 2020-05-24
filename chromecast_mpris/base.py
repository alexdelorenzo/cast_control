from typing import Optional
from enum import auto

import pychromecast

from mpris_server.base import AutoName

RC_NO_CHROMECAST = 1
NO_DURATION = 0
NO_DELTA = 0

DESKTOP_FILE = "chromecast_mpris.desktop"
DEFAULT_THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Chromecast_cast_button_icon.svg/500px-Chromecast_cast_button_icon.svg.png'

YOUTUBE = "YouTube"


class ChromecastMediaType(AutoName):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


def get_chromecast(name: str) -> Optional[pychromecast.Chromecast]:
  chromecasts = pychromecast.get_chromecasts()

  if not name:
    return chromecasts[0] if chromecasts else None

  name = name.lower()

  for chromecast in chromecasts:
    if chromecast.name.lower() == name:
      chromecast.wait()
      return chromecast
