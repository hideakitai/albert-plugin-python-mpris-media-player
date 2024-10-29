# albert-media-player

[Albert](https://albertlauncher.github.io/) Python plugin to control media players (spotify, mpv, vlc, browsers, etc.) via [MPRIS](https://specifications.freedesktop.org/mpris-spec/latest/fullindex.html)

## Dependencies

- `dbus-python` (will be automatically installed into albert venv)

## Usage

- Clone this repo into the user plugin directory
  - Default: `~/.local/share/albert/python/plugins` for Ubuntu
- Open Albert settings and enable:
  - Plugins > Python Plugins
  - Plugins > MPRIS Media Player
- Control media players by using:
  - `mp <your-queries>`

## Supported Commands

- `play`: Play current track
- `pause`: Pause current track
- `next`: Go to next track
- `prev`: Go to previous track
- `shuffle`: Toggle shuffle mode
- `loop`: Cycle loop mode
- `goto`: Go to specific position `MM:SS`
- `switch`: Switch to another media player (default: `spotify`)

## LICENSE

MIT
