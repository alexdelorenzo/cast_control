# 📺 Control Chromecasts from Linux
`cast_control` is [a daemon](https://en.wikipedia.org/wiki/Daemon_(computing)) utility that allows you to control media playback on casting devices from the Linux desktop.

While this service runs, it collects data about the media and apps playing on your casting devices and displays it on your computer.

### Integrations
`cast_control` controls Chromecasts and casting devices via D-Bus and [MPRIS media player controls](https://specifications.freedesktop.org/mpris-spec/2.2/). 

MPRIS is the standard media player interface on Linux desktops. 

MPRIS integration is [enabled by default](https://github.com/KDE/plasma-workspace/tree/master/applets/mediacontroller) in Plasma Desktop, and, along with GNOME's volume control widget, [there are widgets for GNOME](https://extensions.gnome.org/extension/1379/mpris-indicator-button/), too. [`playerctl` provides a CLI](https://github.com/altdesktop/playerctl) for controlling media players through MPRIS.

Check out [▶️mpris_server](https://github.com/alexdelorenzo/mpris_server) if you want to integrate MPRIS support into your media player.

## Screenshots
Controlling a Chromecast via Plasma Desktop's Media Player widget:

<img src="https://github.com/alexdelorenzo/chromecast_mpris/raw/name_change/cast_control/assets/mpris_widget.png" height="225" /> <img src="https://github.com/alexdelorenzo/chromecast_mpris/raw/name_change/cast_control/assets/mpris_plasma.png" height="225" />

## Features
  * [x] Control music and video playback
  * [x] Control app playback
  * [x] View playback information in real-time
  * [x] Display thumbnail and title
  * [x] Display playback position and media length
  * [x] Seek forward and backward
  * [x] Play, pause, and stop playback
  * [x] Volume up and down
  * [x] Play next and previous
  * [x] Quit casted app
  * [x] Open media from D-Bus
  * [x] Play YouTube videos
  * [ ] Playlist integration

## Installation
### Requirements
 - Linux / *BSD / [macOS](https://github.com/zbentley/dbus-osx-examples)
 - [D-Bus](https://www.freedesktop.org/wiki/Software/dbus/)
 - Python >= 3.7
 - [PyGObject](https://pypi.org/project/PyGObject/)
 - `requirements.txt`
 
#### Installing PyGObject
On Debian-derived distributions like Ubuntu, install `python3-gi` with `apt`. 

On Arch, you'll want to install `python-gobject`, or install `cast_control` [directly from the AUR](https://aur.archlinux.org/packages/cast_control/).

On macOS, install [`pygobject3`](https://formulae.brew.sh/formula/pygobject3) via `brew`.

Use `pip` to install `PyGObject>=3.34.0` if there are no installation candidates available in your vendor's package repositories.

### PyPI
```bash
$ python3 -m pip install cast_control
```

You'll get a `cast_control` executable added to your `$PATH`.

### GitHub
Check out [the releases page on GitHub](https://github.com/alexdelorenzo/cast_control/releases) for stable releases.

If you'd like to use the development branch, clone the repository.

Once you have a source copy, run `python3 -m pip install -r requirements.txt`, followed by `python3 setup.py install`. 

You'll get a `cast_control` executable added to your `$PATH`.

### AUR
If you're on Arch, you can install `cast_control` [directly from the AUR](https://aur.archlinux.org/packages/cast_control/). Thanks, [@yochananmarqos](https://github.com/yochananmarqos)!

```bash
$ yay -S cast_control
```

### Upgrades
Stable releases are uploaded to PyPI. You can upgrade your `cast_control` installation like so:

```bash
$ python3 -m pip --upgrade cast_control
```

See the [releases page](https://github.com/alexdelorenzo/cast_control/releases) on GitHub.

## Usage
You'll need to make sure that your computer can make network connections with your casting devices. It also helps to know the names of the devices in advance.

### Launch
Installing the package via PyPI, GitHub or the AUR will add `cast_control` to your `pip` executables path:
```bash
$ which cast_control 
~/.local/bin/cast_control
```

If you have your `pip` executables path added to your shell's `$PATH`, you can launch `cast_control` like so:
```bash
$ cast_control --help
```

Or, using the short name launcher `castctl`:
```bash
$ castctl --help
```

You can also launch `cast_control` via its Python module. This can be useful if your `$PATH` doesn't point to your `pip` executables.
```bash
$ python3 -m cast_control --help
```

### Help
#### Shell completion
To enable Bash completion for `cast_control`, add the following to your `~/.bashrc`:
```bash
eval "$(_CAST_CONTROL_COMPLETE=bash_source cast_control)"
```

For the `zsh` and `fish` shells, check out [the documentation here](https://click.palletsprojects.com/en/8.0.x/shell-completion/#enabling-completion).

#### Help text
```bash
$ cast_control --help
Usage: cast_control [OPTIONS] COMMAND [ARGS]...

  Control casting devices via Linux media controls and desktops.

  This daemon connects your casting device directly to the D-Bus media player
  interface.

  See https://github.com/alexdelorenzo/cast_control for more information.

Options:
  -L, --license  Show license and copyright information.
  -V, --version  Show version information.
  --help         Show this message and exit.

Commands:
  connect  Connect to the device and run the service in the foreground.
  service  Connect, disconnect or reconnect the background service to or...
```

##### `connect` command
```bash
$ cast_control connect --help
Usage: cast_control connect [OPTIONS]

  Connect to the device and run the service in the foreground.

Options:
  -n, --name TEXT         Connect to a device via its name, otherwise control
                          the first device found.
  -h, --host TEXT         Connect to a device via its hostname or IP address,
                          otherwise control the first device found.
  -u, --uuid TEXT         Connect to a device via its UUID, otherwise control
                          the first device found.
  -w, --wait FLOAT        Seconds to wait between trying to make initial
                          successful connections to a device.
  -r, --retry-wait FLOAT  Seconds to wait between reconnection attempts if a
                          successful connection is interrupted.  [default:
                          5.0]
  -i, --icon              Use a lighter icon instead of the dark icon. The
                          lighter icon goes well with dark themes.  [default:
                          False]
  -l, --log-level TEXT    Set the debugging log level.  [default: WARN]
  --help                  Show this message and exit.
```

##### `service` command
```bash
$ cast_control service --help
Usage: cast_control service [OPTIONS] COMMAND [ARGS]...

  Connect, disconnect or reconnect the background service to or from your
  device.

Options:
  --help  Show this message and exit.

Commands:
  connect     Connect the background service to the device.
  disconnect  Disconnect the background service from the device.
  reconnect   Reconnect the background service to the device.
  log         Show the service log.
```

###### `service connect` command
```bash
$ cast_control service connect --help
Usage: cast_control service connect [OPTIONS]

  Connect the background service to the device.

Options:
  -n, --name TEXT         Connect to a device via its name, otherwise control
                          the first device found.
  -h, --host TEXT         Connect to a device via its hostname or IP address,
                          otherwise control the first device found.
  -u, --uuid TEXT         Connect to a device via its UUID, otherwise control
                          the first device found.
  -w, --wait FLOAT        Seconds to wait between trying to make initial
                          successful connections to a device.
  -r, --retry-wait FLOAT  Seconds to wait between reconnection attempts if a
                          successful connection is interrupted.  [default:
                          5.0]
  -i, --icon              Use a lighter icon instead of the dark icon. The
                          lighter icon goes well with dark themes.  [default:
                          False]
  -l, --log-level TEXT    Set the debugging log level.  [default: WARN]
  --help                  Show this message and exit.
```

### Connect to a device
Connect to a device named "My Device":
```bash
$ cast_control connect --name "My Device"
```

Connect to a device named "My Device" and run `cast_control` in the background:
```bash
$ cast_control service connect --name "My Device"
```

After launching `cast_control`, you can use any MPRIS client to interact with it. MPRIS support is built in directly to Plasma Desktop and GNOME 3, and you can use `playerctl` on the command-line. 

### Retry until a Chromecast is found
You can use the `-w/--wait` flag to specify a waiting period in seconds before `cast_control` will try to find a casting device again if one is not found initially.

For example, if you want to wait 60 seconds between scans for devices, you can run the following:
```bash
$ export SECONDS=60
$ cast_control connect --wait $SECONDS
# or
$ cast_control service connect --wait $SECONDS
```

This is useful if you'd like to start `cast_control` at login, and there is a chance that your device isn't on, or you're on a different network. 

### Reconnect or disconnect the background service
If the background service is running, you can force it to reconnect and restart, or to disconnect it entirely.
```bash
$ cast_control service reconnect
# or
$ cast_control service disconnect
```

### Open a URI on a Chromecast
 Get the D-Bus name for your device using `playerctl`.
```bash
$ playerctl --list-all
My_Device
```

Use the D-Bus name to issue commands to it.
```bash
$ export URL="http://ccmixter.org/content/gmz/gmz_-_Parametaphoriquement.mp3"
$ playerctl --player My_Device open "$URL"
```

This will play a song on your device.

### Open a YouTube video
You can cast YouTube videos the same way you can cast a generic URI.
```bash
$ export VIDEO="https://www.youtube.com/watch?v=I4nkgJdVZFA"
$ playerctl --player My_Device open "$VIDEO"
```

### Logs
You can set the log level using the `-l/--log-level` flag with the `connect` or `service connect` commands:
```bash
$ cast_control connect --log-level debug
```

Here's a [list of log levels supported by `cast_control`](https://docs.python.org/3/library/logging.html#logging-levels).

You can view the background service's log file with the `service log` command:
```bash
$ cast_control service log
```

## Support
Want to support this project and [other open-source projects](https://github.com/alexdelorenzo) like it?

<a href="https://www.buymeacoffee.com/alexdelorenzo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" height="60px" style="height: 60px !important;width: 217px !important;max-width:25%" ></a>

## License
See `LICENSE`. If you'd like to use this project with a different license, please get in touch.
