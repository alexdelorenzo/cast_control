from typing import List, NamedTuple, Optional

import pychromecast

from mpris_server.adapter import PlayState, Track


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