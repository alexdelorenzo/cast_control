# 📺 Control Chromecasts with MPRIS
Control your Chromecast via [MPRIS media player controls](https://specifications.freedesktop.org/mpris-spec/2.2/). MPRIS is the standard media player interface on Linux desktops.
`chromecast_mpris` allows you to control media playback on Chromecasts, and provides an interface for playback information.

MPRIS integration is [enabled by default](https://github.com/KDE/plasma-workspace/tree/master/applets/mediacontroller) in Plasma Desktop, and, along with GNOME's volume control widget, [there are widgets for GNOME](https://extensions.gnome.org/extension/1379/mpris-indicator-button/), too. [`playerctl` provides a CLI](https://github.com/altdesktop/playerctl) for controlling media players through MPRIS.

Check out [▶️mpris_server](https://github.com/alexdelorenzo/mpris_server) if you want to integrate MPRIS support into your media player.

## Screenshots

Controlling a Chromecast via Plasma Desktop's Media Player widget:

<img src="https://github.com/alexdelorenzo/chromecast_mpris/raw/master/assets/mpris_widget.png" height="350" /> <img src="https://github.com/alexdelorenzo/chromecast_mpris/raw/master/assets/mpris_bar.png" height="350" />


## Features
  * [x] Control generic music and video playback
  * [x] Control app playback
  * [x] View playback information in real-time
  * [x] Display thumbnail and title
  * [x] Display playback position and media end
  * [x] Seek forward and backward
  * [x] Play / Pause / Stop
  * [x] Volume up and down
  * [x] Play next and previous
  * [x] Quit Chromecast app
  * [x] Open media from MPRIS
  * [ ] Playlist integration

## Installation
### Requirements
 - Linux / *BSD / [macOS](https://github.com/zbentley/dbus-osx-examples)
 - DBus
 - Python >= 3.6
 - [PyGObject](https://pypi.org/project/PyGObject/)
 - `requirements.txt`
 
#### Installing PyGObject
On Debian-derived distributions like Ubuntu, install `python3-gi` with `apt`. On Arch, you'll want to install `python-gobject`. On macOS, install [`pygobject3`](https://formulae.brew.sh/formula/pygobject3) via `brew`.

Use `pip` to install `PyGObject>=3.34.0` if there are no installation candidates available in your vendor's package repositories.

### PyPI
`pip3 install chromecast_mpris`

You'll get a `chromecast_mpris` executable added to your `$PATH`.


### Github
Clone the repo, run `pip3 install -r requirements.txt`, followed by `python3 setup.py install`. 

You'll get a `chromecast_mpris` executable added to your `$PATH`.

## Usage
You'll need to make sure that your computer is on the same network as your Chromecasts, and that you're able to make connections to them. 

It also helps to know the names of the devices in advance.

### Example
#### Help
```bash
$ chromecast_mpris --help
Usage: command.py [OPTIONS]

  Control Chromecasts through MPRIS media controls.

Options:
  -n, --name TEXT          Specify Chromecast, otherwise control first
                           Chromecast found.
  -l, --log-level INTEGER  Debugging log level.  [default: 20]
  --help                   Show this message and exit.
```

#### Connecting to a Device
Connect to Chromecast named "MyChromecast" and run the adapter in the background.
```bash
$ chromecast_mpris -n MyChromecast &
[1] 1234
```

## License
See `LICENSE`. Message me if you'd like to use this project with a different license.
