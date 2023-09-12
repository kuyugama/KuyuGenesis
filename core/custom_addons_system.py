from pathlib import Path
from typing import Callable

from RelativeAddonsSystem import RelativeAddonsSystem, Addon
from kgemng import CommandManager, EventManager


class CustomRelativeAddonsSystem(RelativeAddonsSystem):

    def __init__(self, addons_directory: str | Path, auto_install_dependencies: bool = False):
        super().__init__(addons_directory, auto_install_dependencies)

        self._main_addon = None

    def set_main_addon(self, addon: Addon):
        if not isinstance(addon, Addon):
            raise ValueError("Cannot set main addon of type {type}".format(type=type(addon)))

        self._main_addon = addon

    def get_main_addon(self):
        return self._main_addon

    def get_addon_event_manager(self, name: str | Addon) -> EventManager:
        addon = self.get_addon_by_name(name)

        if not addon:
            raise ValueError("Cannot find this addon")

        module = addon.module

        if not hasattr(module, "get_event_manager"):
            raise AttributeError("Module hasn't event manager")

        return module.get_event_manager()

    def get_addon_command_manager(self, name: str | Addon) -> CommandManager | None:
        addon = self.get_addon_by_name(name)

        if not addon:
            raise ValueError("Cannot find this addon")

        module = addon.module

        if not hasattr(module, "get_command_manager"):
            raise AttributeError("Module hasn't command manager")

        return module.get_command_manager()

    def get_addon_system_event_handler(self, name: str | Addon, event: str = "load") -> Callable[[], None]:
        addon = self.get_addon_by_name(name)

        if not addon:
            raise ValueError("Cannot find this addon")

        module = addon.module

        event_handler_name = "on_{event}".format(event=event)

        if not hasattr(module, event_handler_name):
            raise AttributeError("Module hasn't handler for event '{event}'".format(event=event))

        return getattr(module, event_handler_name)
