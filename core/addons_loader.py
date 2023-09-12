import logging
from pathlib import Path

from RelativeAddonsSystem import Addon
from colorama import Fore

import config
from core.custom_addons_system import CustomRelativeAddonsSystem
from kgemng import CommandManager, EventManager
from core.logs import get_logger, wrap_into_color

logger = get_logger("AddonLoader", logging.INFO)

system = CustomRelativeAddonsSystem(
    config.addons_root, config.auto_install_dependencies
)

MAIN_COMMAND_MANAGER: CommandManager | None = None
MAIN_EVENT_MANAGER: EventManager | None = None

LOADED_ADDONS: set[Addon] = set()


def init(main_command_manager: CommandManager, main_event_manager: EventManager):
    global MAIN_COMMAND_MANAGER, MAIN_EVENT_MANAGER
    MAIN_COMMAND_MANAGER = main_command_manager
    MAIN_EVENT_MANAGER = main_event_manager


def load_main_addon():
    addon = Addon(Path(__file__).parent / "MainAddon")

    load_addons(addon)


def load_addons(
    *addons_names: str | Addon
):
    if not len(addons_names):
        return

    for addon_name in addons_names:
        addon = system.get_addon_by_name(addon_name)

        if not addon:
            logger.warn(
                "Addon [ {addon_name} ] not found".format(
                    addon_name=wrap_into_color(addon_name, color=Fore.YELLOW)
                )
            )
            continue

        if addon.meta.status == "disabled":
            logger.warn(
                "Cannot load disabled addons [ {addon_name} ]".format(
                    addon_name=wrap_into_color(addon_name, color=Fore.YELLOW)
                )
            )
            continue

        try:
            system.get_addon_system_event_handler(addon, "load")()
        except AttributeError:
            pass

        LOADED_ADDONS.add(addon)

        include_events(addon)
        include_commands(addon)


def unload_addons(*addons_names: str | Addon):
    if not len(addons_names):
        return

    for addon_name in addons_names:
        addon = system.get_addon_by_name(addon_name)

        if not addon:
            logger.warn(
                "Addon [ {addon_name} ] not found".format(
                    addon_name=wrap_into_color(addon_name, color=Fore.YELLOW)
                )
            )
            continue

        if addon.meta.status == "disabled":
            logger.warn(
                "Cannot unload disabled addon [ {addon_name} ]".format(
                    addon_name=wrap_into_color(addon_name, color=Fore.YELLOW)
                )
            )
            continue

        if addon not in LOADED_ADDONS:
            logger.warning(
                "Cannot unload not loaded addon [ {addon_name} ]".format(
                    addon_name=wrap_into_color(addon_name, color=Fore.YELLOW)
                )
            )

        try:
            system.get_addon_system_event_handler(addon, "unload")()
        except AttributeError:
            pass

        LOADED_ADDONS.remove(addon)

        exclude_events(addon)
        exclude_commands(addon)


def include_events(*addons_names: str | Addon):
    addons = []
    if len(addons_names):
        for name in addons_names:
            addon = system.get_addon_by_name(name)
            if not addon:
                logger.warn(
                    "Addon [ {addon_name} ] not found".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            if addon.meta.status == "disabled":
                logger.warn(
                    "Cannot include event manager from disabled addons [ {addon_name} ]".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            addons.append(addon)

    else:
        addons = system.get_enabled_addons()

    for addon in addons:
        try:
            event_manager = system.get_addon_event_manager(addon)
            event_manager.enable()
        except Exception as e:
            logger.warn(
                "Error while including event manager from addon [ {addon_name} ] -> ".format(
                    addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
                )
                + wrap_into_color(e.args[0], color=Fore.RED)
            )
            continue

        if not MAIN_EVENT_MANAGER:
            logging.critical("Loader doesn't initiated")

        MAIN_EVENT_MANAGER.include_manager(event_manager)
        logger.info(
            "Included event manager from addon [ {addon_name} ]".format(
                addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
            )
        )


def exclude_events(*addons_names: str | Addon):
    addons = set()
    if len(addons_names):
        for name in addons_names:
            addon = system.get_addon_by_name(name)
            if not addon:
                logger.warn(
                    "Addon [ {addon_name} ] not found".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            if addon.meta.status == "disabled":
                logger.warn(
                    "Cannot exclude event manager from disabled addons [ {addon_name} ]".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            addons.add(addon)

    else:
        logger.warning("At least one addon must be passed to exclude event manager from it")
        return

    for addon in addons:
        try:
            event_manager = system.get_addon_event_manager(addon)
            event_manager.disable()
        except Exception as e:
            logger.warn(
                "Error while including event manager from addon [ {addon_name} ] -> ".format(
                    addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
                )
                + wrap_into_color(e.args[0], color=Fore.RED)
            )
            continue

        if not MAIN_EVENT_MANAGER:
            logging.critical("Loader doesn't initiated")

        MAIN_EVENT_MANAGER.exclude_manager(event_manager)
        logger.info(
            "Excluded event manager from addon [ {addon_name} ]".format(
                addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
            )
        )


def include_commands(*addons_names: str | Addon):
    addons = []
    if len(addons_names):
        for name in addons_names:
            addon = system.get_addon_by_name(name)
            if not addon:
                logger.warn(
                    "Addon [ {addon_name} ] not found".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            if addon.meta.status == "disabled":
                logger.warn(
                    "Cannot include command managers from disabled addons [ {addon_name} ]".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            addons.append(addon)

    else:
        addons = system.get_enabled_addons()

    for addon in addons:
        try:
            addon_command_manager = system.get_addon_command_manager(addon)
            addon_command_manager.enable()
        except Exception as e:
            logger.warn(
                "Error while including command managers from addon [ {addon_name} ] -> ".format(
                    addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
                )
                + wrap_into_color(e.args[0], color=Fore.RED)
            )
            return

        if not MAIN_COMMAND_MANAGER:
            logging.critical("Loader doesn't initiated")

        MAIN_COMMAND_MANAGER.include_manager(addon_command_manager)
        logger.info(
            "Included command manager from addon [ {name} ]".format(
                name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
            )
        )


def exclude_commands(*addons_names: str | Addon):
    addons = []
    if len(addons_names):
        for name in addons_names:
            addon = system.get_addon_by_name(name)
            if not addon:
                logger.warn(
                    "Addon [ {addon_name} ] not found".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            if addon.meta.status == "disabled":
                logger.warn(
                    "Cannot exclude command managers from disabled addons [ {addon_name} ]".format(
                        addon_name=wrap_into_color(name, color=Fore.YELLOW)
                    )
                )
                continue

            addons.append(addon)

    else:
        logger.warning("At least one addon must be passed to exclude command manager from it")
        return

    for addon in addons:
        try:
            addon_command_manager = system.get_addon_command_manager(addon)
            addon_command_manager.disable()
        except Exception as e:
            logger.warn(
                "Error while excluding command manager from addon [ {addon_name} ] -> ".format(
                    addon_name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
                )
                + wrap_into_color(e.args[0], color=Fore.RED)
            )
            return

        if not MAIN_COMMAND_MANAGER:
            logging.critical("Loader doesn't initiated")

        MAIN_COMMAND_MANAGER.exclude_manager(addon_command_manager)
        logger.info(
            "Excluded command manager from addon [ {name} ]".format(
                name=wrap_into_color(addon.meta.name, color=Fore.YELLOW)
            )
        )


def enable_addon(addon_name: str | Addon, load_managers: bool = False):
    addon = system.get_addon_by_name(addon_name)

    if not addon:
        logger.warning("Addon [ {addon_name} ] not found".format(addon_name=addon_name))
        return

    addon.enable()

    try:
        system.get_addon_system_event_handler(addon, "enable")()
    except AttributeError:
        pass

    if load_managers:
        include_commands(addon)
        include_events(addon)

    return True


def disable_addon(addon_name: str | Addon, unload_managers: bool = True):
    addon = system.get_addon_by_name(addon_name)

    if not addon:
        logger.warning("Addon [ {addon_name} ] not found".format(addon_name=addon_name))
        return

    try:
        system.get_addon_system_event_handler(addon, "disable")()
    except AttributeError:
        pass

    if unload_managers:
        exclude_commands(addon)
        exclude_events(addon)

    addon.disable()

    return True
