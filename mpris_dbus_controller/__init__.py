from typing import Any, Optional

import dbus
from dbus.mainloop.glib import DBusGMainLoop

INTERFACE = "org.mpris.MediaPlayer2.Player"


class MPRISDBusController:
    def __init__(self, bus_app: str = "spotify") -> None:
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.bus_app = bus_app
        self.proxy = None
        self.interface = None
        self.properties = None
        if self.is_current_bus_app_available():
            self.activate_current_bus_app()

    # Bus Connection
    def _get_available_bus_names(self) -> list[str]:
        """Get a list of available media player bus names"""
        try:
            proxy = self.bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
            interface = dbus.Interface(proxy, "org.freedesktop.DBus")
            services = interface.ListNames()
            names = [s for s in services if s.startswith("org.mpris.MediaPlayer2.")]
            return [name for name in names if not (name.startswith(":") or "instance" in name)]
        except Exception as e:
            print(f"Error getting available media players: {e}")
            return []

    def get_available_bus_apps(self) -> list[str]:
        """Get a list of available media player bus apps"""
        return [name.split(".")[-1] for name in self._get_available_bus_names()]

    def get_current_bus_app(self) -> str:
        """Get the bus app of the media player"""
        return self.bus_app

    def activate_bus_app(self, bus_app: str) -> None:
        """Set the bus name of the media player"""
        try:
            self.proxy = self.bus.get_object(f"org.mpris.MediaPlayer2.{self.bus_app}", "/org/mpris/MediaPlayer2")
            self.interface = dbus.Interface(self.proxy, INTERFACE)
            self.properties = dbus.Interface(self.proxy, "org.freedesktop.DBus.Properties")
        except Exception as e:
            print(f"Error connecting to media player '{bus_app}': {e}")

    def is_bus_app_available(self, app: str) -> bool:
        """Check if the media player is available"""
        return app in self.get_available_bus_apps()

    def is_current_bus_app_available(self) -> bool:
        """Check if the current media player is available"""
        return self.is_bus_app_available(self.bus_app)

    def is_current_bus_app_active(self) -> bool:
        """Check if the current media player is active"""
        return self.is_current_bus_app_available() and self.proxy is not None

    def activate_current_bus_app(self) -> None:
        """Activate the current media player"""
        self.activate_bus_app(self.bus_app)

    def deactivate_bus_app(self) -> None:
        """Deactivate the current media player"""
        self.proxy = None
        self.interface = None
        self.properties = None

    # Playback Controls
    def play(self) -> None:
        """Start playback"""
        if self.interface is not None:
            self.interface.Play()

    def pause(self) -> None:
        """Pause playback"""
        if self.interface is not None:
            self.interface.Pause()

    def play_pause(self) -> None:
        """Toggle play/pause"""
        if self.interface is not None:
            self.interface.PlayPause()

    def stop(self) -> None:
        """Stop playback"""
        if self.interface is not None:
            self.interface.Stop()

    def next_track(self) -> None:
        """Skip to next track"""
        if self.interface is not None:
            self.interface.Next()

    def previous_track(self) -> None:
        """Go back to previous track"""
        if self.interface is not None:
            self.interface.Previous()

    # Player Status
    def get_playback_status(self) -> str:
        """Get current playback status (Playing/Paused/Stopped)"""
        if self.properties is None:
            return "Stopped"
        return str(self.properties.Get(INTERFACE, "PlaybackStatus"))

    def get_position(self) -> int:
        """Get current playback position in microseconds"""
        if self.properties is None:
            return 0
        return self.properties.Get(INTERFACE, "Position")

    def get_position_str(self) -> str:
        """Get current playback position in human-readable format (MM:SS)"""
        metadata = self.get_metadata()
        if metadata is None:
            return "00:00:00"
        position = self.get_position() / 1_000_000
        minutes = int(position // 60)
        seconds = int(position % 60)
        return f"{minutes:02}:{seconds:02}"

    def get_position_and_length_str(self) -> str:
        """Get current playback position/length in human-readable format (MM:SS/MM:SS)"""
        metadata = self.get_metadata()
        if metadata is None:
            return "00:00/00:00"
        position = self.get_position() / 1_000_000
        minutes = int(position // 60)
        seconds = int(position % 60)
        length: Optional[Any] = metadata.get("length")
        full_position = length / 1_000_000 if length else 0
        full_minutes = int(full_position // 60)
        full_seconds = int(full_position % 60)
        return f"{minutes:02}:{seconds:02}/{full_minutes:02}:{full_seconds:02}"

    def set_position(self, position) -> None:
        """Set playback position for the current track"""
        if self.interface is None:
            return
        metadata = self.get_metadata()
        if metadata is not None:
            track_id = metadata.get("track_id")
            self.interface.SetPosition(track_id, position)

    def set_position_str(self, position_str: str) -> None:
        """Set playback position for the current track using a human-readable format (MM:SS)"""
        minutes, seconds = map(int, position_str.split(":"))
        position = (minutes * 60 + seconds) * 1_000_000
        self.set_position(position)

    # Playback Mode Settings
    def set_shuffle(self, shuffle_status: bool) -> None:
        """Set shuffle mode (True/False)"""
        if self.properties is not None:
            self.properties.Set(INTERFACE, "Shuffle", shuffle_status)

    def get_shuffle(self) -> bool:
        """Get current shuffle mode status"""
        if self.properties is None:
            return False
        return bool(self.properties.Get(INTERFACE, "Shuffle"))

    def set_loop(self, loop_status: str) -> None:
        """Set repeat mode (None/Track/Playlist)"""
        if self.properties is not None:
            self.properties.Set(INTERFACE, "LoopStatus", loop_status)

    def get_loop(self) -> str:
        """Get current loop status"""
        if self.properties is None:
            return "None"
        return str(self.properties.Get(INTERFACE, "LoopStatus"))

    def cycle_loop(self) -> None:
        """Cycle repeat mode (None -> Track -> Playlist)"""
        if self.properties is not None:
            LOOP_STATES = ["None", "Track", "Playlist"]
            loop = self.get_loop()
            loop_index = LOOP_STATES.index(loop)
            loop_status = LOOP_STATES[(loop_index + 1) % len(LOOP_STATES)]
            self.properties.Set(INTERFACE, "LoopStatus", loop_status)

    # Metadata Retrieval
    def get_metadata(self) -> Optional[dict[str, Any]]:
        """Get detailed information about the current track"""
        if self.properties is None:
            return None
        metadata = self.properties.Get(INTERFACE, "Metadata")
        return {
            "title": str(metadata.get("xesam:title", "Unknown")),
            "artist": str(metadata.get("xesam:artist", ["Unknown"])[0]),
            "album": str(metadata.get("xesam:album", "Unknown")),
            "album_artist": str(metadata.get("xesam:albumArtist", ["Unknown"])[0]),
            "track_number": int(metadata.get("xesam:trackNumber", 0)),
            "url": str(metadata.get("xesam:url", "")),
            "art_url": str(metadata.get("mpris:artUrl", "")),
            "length": int(metadata.get("mpris:length", 0)),
            "track_id": str(metadata.get("mpris:trackid", "")),
        }

    def get_title(self) -> str:
        """Get a title of the current track metadata"""
        metadata = self.get_metadata()
        if metadata is None:
            return "-"
        return metadata["title"]

    def get_artist(self) -> str:
        """Get an artist of the current track metadata"""
        metadata = self.get_metadata()
        if metadata is None:
            return "-"
        return metadata["artist"]

    def get_album(self) -> str:
        """Get an album of the current track metadata"""
        metadata = self.get_metadata()
        if metadata is None:
            return "-"
        return metadata["album"]

    def get_album_artist(self) -> str:
        """Get an album artist of the current track metadata"""
        metadata = self.get_metadata()
        if metadata is None:
            return "-"
        return metadata["album_artist"]

    def get_art_url(self) -> str:
        """Get an album art URL of the current track metadata"""
        metadata = self.get_metadata()
        if metadata is None:
            return ""
        return metadata["art_url"]


if __name__ == "__main__":
    controller = MPRISDBusController()

    print(f"Playback status: {controller.get_playback_status()}")
    print(f"Position: {controller.get_position()}")
    print(f"Position (MM:SS): {controller.get_position_str()}")
    print(f"Position/Length (MM:SS/MM:SS): {controller.get_position_and_length_str()}")
    print(f"Shuffle status: {controller.get_shuffle()}")
    print(f"Loop status: {controller.get_loop()}")
    print(f"Metadata: {controller.get_metadata()}")
