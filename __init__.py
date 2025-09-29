import os
import sys
from typing import Any, List, Optional

from albert import Action, PluginInstance, StandardItem, TriggerQueryHandler

# NOTE: workaround for importing local module in albert
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
from mpris_dbus_controller import MPRISDBusController

md_iid = "3.1"
md_version = "1.1"
md_name = "MPRIS Media Player"
md_description = "Python plugin to control media players via MPRIS"
md_license = "MIT"
md_url = "https://github.com/hideakitai/albert-plugin-python-mpris-media-player"
md_authors = ["@hideakitai"]
# md_bin_dependencies = []
md_lib_dependencies = ["dbus-python"]
# md_platforms = ["linux"]

DEFAULT_TRIGGER = "mp "
DEFAULT_BUS_NAME = "spotify"
ICONS = {
    "generic": "xdg:audio-x-generic-symbolic",
    "play": "xdg:media-playback-start-symbolic",
    "pause": "xdg:media-playback-pause-symbolic",
    "next": "xdg:media-skip-forward-symbolic",
    "previous": "xdg:media-skip-backward-symbolic",
    "shuffle": "xdg:media-playlist-shuffle-symbolic",
    "loop": "xdg:media-playlist-repeat-symbolic",
    "goto": "xdg:go-jump-symbolic",
    "switch": "xdg:media-eject-symbolic",
    "toggle": "xdg:media-playback-start-symbolic",
    "stop": "xdg:media-playback-stop-symbolic",
    "error": "xdg:dialog-error-symbolic",
}


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)
        self.controller = MPRISDBusController(DEFAULT_BUS_NAME)

    def id(self) -> str:
        return md_name

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def defaultTrigger(self) -> str:
        return DEFAULT_TRIGGER

    def create_commands(self) -> dict[str, tuple[str, str, Any, List[str]]]:
        return {
            "info": (
                f"{self.controller.get_playback_status()} | {self.controller.get_title()}",
                f"{self.controller.get_album_artist()} / {self.controller.get_album()}",
                lambda: self.controller.play_pause(),
                [self.controller.get_art_url(), ICONS["generic"]],
            ),
            "play": (
                "Play",
                "Play current track",
                lambda: self.controller.play(),
                [ICONS["play"]],
            ),
            "pause": (
                "Pause",
                "Pause current track",
                lambda: self.controller.pause(),
                [ICONS["pause"]],
            ),
            "next": (
                "Next",
                "Go to next track",
                lambda: self.controller.next_track(),
                [ICONS["next"]],
            ),
            "prev": (
                "Previous",
                "Go to previous track",
                lambda: self.controller.previous_track(),
                [ICONS["previous"]],
            ),
            "shuffle": (
                "Shuffle",
                f"Toggle shuffle mode ({self.controller.get_shuffle()})",
                lambda: self.controller.set_shuffle(self.controller.get_shuffle() is False),
                [ICONS["shuffle"]],
            ),
            "loop": (
                "Loop",
                f"Cycle loop mode ({self.controller.get_loop()})",
                lambda: self.controller.cycle_loop(),
                [ICONS["loop"]],
            ),
            "goto": (
                "GoTo",
                f"Go to specific position MM:SS ({self.controller.get_position_str()})",
                lambda: None,
                [ICONS["goto"]],
            ),
            "switch": (
                "Switch",
                f"Switch to another media player ({self.controller.get_current_bus_app()})",
                lambda: None,
                [ICONS["switch"]],
            ),
            # "toggle": (
            #     "Toggle",
            #     f"Toggle Play/Pause ({self.controller.get_playback_status()})",
            #     lambda: self.controller.play_pause(),
            #     [ICONS["play"]],
            # ),
            # "stop": (
            #     "Stop",
            #     "Stop playback",
            #     lambda: self.controller.stop(),
            #     [ICONS["play"]],
            # ),
        }

    def create_player_not_running_item(self) -> StandardItem:
        return StandardItem(
            id=md_name,
            text=f"MEDIA PLAYER NOT RUNNING: {self.controller.get_current_bus_app()}",
            subtext=f"Please (re)start '{self.controller.get_current_bus_app()}' first",
            iconUrls=[ICONS["error"]],
        )

    def create_command_item(self, cmd, text, subtext, func, icons) -> StandardItem:
        return StandardItem(
            id=f"{md_name}_{cmd}",
            text=text,
            subtext=f"{subtext}",
            iconUrls=icons,
            actions=[Action("Execute", text, func)],
        )

    def create_app_item(self, player) -> StandardItem:
        return StandardItem(
            id=f"{md_name}_{player}",
            text=f"{player}",
            subtext=f"Switch media player to '{player}'",
            iconUrls=[ICONS["generic"]],
            actions=[Action("Switch", f"{player}", lambda p=player: self.controller.activate_bus_app(p))],
        )

    def create_goto_item(self, maybe_pos: Optional[str]) -> StandardItem:
        pos = "00:00" if maybe_pos is None else maybe_pos
        curr_pos = self.controller.get_position_str()
        return StandardItem(
            id=f"{md_name}_goto",
            text=f"Go to {pos}",
            subtext=f"Go to '{curr_pos}' -> '{pos}'",
            iconUrls=[ICONS["goto"]],
            actions=[Action("GoTo", f"{pos}", lambda p=pos: self.controller.set_position_str(p))],
        )

    def handleTriggerQuery(self, query):
        items = []
        commands = {}

        if self.controller.is_current_bus_app_active():
            commands = self.create_commands()
        else:
            if self.controller.is_current_bus_app_available():
                self.controller.activate_current_bus_app()
                commands = self.create_commands()
            else:
                self.controller.deactivate_bus_app()
                items.append(self.create_player_not_running_item())
                commands = self.create_commands()
                commands = {k: commands[k] for k in ["switch"]}

        args = query.string.lower().strip().split(" ")
        command = args[0] if len(args) > 0 else None
        if command is None or command == "":
            # Show all commands
            for cmd, (text, subtext, func, icons) in commands.items():
                items.append(self.create_command_item(cmd, text, subtext, func, icons))
        else:
            if command == "switch":
                apps = self.controller.get_available_bus_apps()
                app_name = args[1] if len(args) > 1 else None
                if app_name is None:
                    # List all players
                    for app in apps:
                        items.append(self.create_app_item(app))
                else:
                    # Filter player by bus_name
                    for app in apps:
                        if app.startswith(app_name):
                            items.append(self.create_app_item(app))
            elif command == "goto":
                pos = args[1] if len(args) > 1 else None
                items.append(self.create_goto_item(pos))
            else:
                # Filter commands based on input
                for cmd, (text, subtext, func, icons) in commands.items():
                    if cmd.startswith(command):
                        items.append(self.create_command_item(cmd, text, subtext, func, icons))

        query.add(items)
