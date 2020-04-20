from enum import auto
from typing import List, NamedTuple, Optional

import pychromecast

from mpris_server.adapter import PlayState, Track, AutoName

DEFAULT_THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Chromecast_cast_button_icon.svg/500px-Chromecast_cast_button_icon.svg.png'


class ChromecastMediaType(AutoName):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


class ChromecastState(NamedTuple):
  name: str
  playstate: PlayState = PlayState.STOPPED
  track: Optional[Track] = None
  volume: float = 1.0


def get_chromecast(name: str) -> Optional[pychromecast.Chromecast]:
  ccs = pychromecast.get_chromecasts()

  for cc in ccs:
    if cc.name.lower() == name.lower():
      cc.wait()
      return cc