import os
import sys
from typing import Any, List, Optional

from albert import Action, PluginInstance, StandardItem, TriggerQueryHandler

# NOTE: workaround for importing local module in albert
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
from mpris_dbus_controller import MPRISDBusController

md_iid = "2.3"
md_version = "1.0"
md_name = "MPRIS Media Player"
md_description = "Python plugin to control media players via MPRIS"
md_license = "MIT"
md_url = "https://github.com/hideakitai/albert-mpris-media-player"
md_authors = "@hideakitai"
# md_bin_dependencies = []
md_lib_dependencies = ["dbus-python"]

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

controller = MPRISDBusController(DEFAULT_BUS_NAME)


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(
            self,
            id=md_name,
            name=md_name,
            description=md_description,
            defaultTrigger=DEFAULT_TRIGGER,
        )

    def create_commands(self) -> dict[str, tuple[str, str, Any, List[str]]]:
        return {
            "info": (
                f"{controller.get_title()}",
                f"{controller.get_album_artist()} / {controller.get_album()}",
                None,
                [controller.get_art_url(), ICONS["generic"]],
            ),
            "play": (
                "Play",
                "Play current track",
                lambda: controller.play(),
                [ICONS["play"]],
            ),
            "pause": (
                "Pause",
                "Pause current track",
                lambda: controller.pause(),
                [ICONS["pause"]],
            ),
            "next": (
                "Next",
                "Go to next track",
                lambda: controller.next_track(),
                [ICONS["next"]],
            ),
            "prev": (
                "Previous",
                "Go to previous track",
                lambda: controller.previous_track(),
                [ICONS["previous"]],
            ),
            "shuffle": (
                "Shuffle",
                f"Toggle shuffle mode ({controller.get_shuffle()})",
                lambda: controller.set_shuffle(controller.get_shuffle() is False),
                [ICONS["shuffle"]],
            ),
            "loop": (
                "Loop",
                f"Cycle loop mode ({controller.get_loop()})",
                lambda: controller.cycle_loop(),
                [ICONS["loop"]],
            ),
            "goto": (
                "GoTo",
                f"Go to specific position MM:SS ({controller.get_position_str()})",
                None,
                [ICONS["goto"]],
            ),
            "switch": (
                "Switch",
                f"Switch to another media player ({controller.get_bus_app()})",
                None,
                [ICONS["switch"]],
            ),
            # "toggle": (
            #     "Toggle",
            #     f"Toggle Play/Pause ({controller.get_playback_status()})",
            #     lambda: controller.play_pause(),
            #     [ICONS["play"]],
            # ),
            # "stop": (
            #     "Stop",
            #     "Stop playback",
            #     lambda: controller.stop(),
            #     [ICONS["play"]],
            # ),
        }

    def create_player_not_running_item(self) -> None:
        StandardItem(
            id=md_name,
            text=f"MEDIA PLAYER NOT RUNNING: {controller.get_bus_app()}",
            subtext=f"Please (re)start '{controller.get_bus_app()}' first",
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
            actions=[Action("Switch", f"{player}", lambda p=player: controller.set_bus_app(p))],
        )

    def create_goto_item(self, maybe_pos: Optional[str]) -> StandardItem:
        pos = "00:00" if maybe_pos is None else maybe_pos
        curr_pos = controller.get_position_str()
        return StandardItem(
            id=f"{md_name}_goto",
            text=f"Go to {pos}",
            subtext=f"Go to '{curr_pos}' -> '{pos}'",
            iconUrls=[ICONS["goto"]],
            actions=[Action("GoTo", f"{pos}", lambda p=pos: controller.set_position_str(p))],
        )

    def handleTriggerQuery(self, query):
        items = []
        commands = self.create_commands()
        if controller.has_active_player() is False:
            items.append(self.create_player_not_running_item())
            commands = {k: commands[k] for k in ["switch"]}

        args = query.string.lower().strip().split(" ")
        command = args[0] if len(args) > 0 else None
        if command is None:
            # Show all commands
            for cmd, (text, subtext, func, icons) in commands.items():
                items.append(self.create_command_item(cmd, text, subtext, func, icons))
        else:
            if command == "switch":
                apps = controller.get_bus_apps()
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
