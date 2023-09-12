""" **This is template addon**

Here you can write code which will be added to created addon via "python create_addon.py"
"""
from pathlib import Path

from RelativeAddonsSystem import Addon
from kgemng import CommandManager, EventManager


this_addon = Addon(Path(__file__).parent)

command_manager = CommandManager(this_addon)
event_manager = EventManager(this_addon)


def get_command_manager():
    return command_manager


def get_event_manager():
    return event_manager

