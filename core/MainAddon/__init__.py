import importlib
import re
from pathlib import Path

from magic_filter import F
from pyrogram import types
from RelativeAddonsSystem import Addon

from kgemng import CommandManager, EventManager, NewMessageEvent
from kgemng.command import Command

from core import addons_loader
from core.account_manager import ExtendedClient, Account

import config


def get_command_manager():
    return command_manager


def get_event_manager():
    return event_manager


this_addon: Addon = Addon(Path(__file__).parent)

command_manager = CommandManager(this_addon, True)

event_manager = EventManager(this_addon, True)


def get_all_included_managers(parent):
    # Temporary store for managers to check
    managers: list[CommandManager] = [parent]
    # Checked managers
    checked_managers = []

    # Fetching all loaded managers
    while len(managers):
        for manager in managers.copy():
            if not manager:
                continue
            checked_managers.append(manager)
            managers.remove(manager)
            managers += manager.get_included_managers()

    return checked_managers


def get_all_command_managers():
    return get_all_included_managers(command_manager.parent)


def get_all_event_managers():
    return get_all_included_managers(event_manager.parent)


@command_manager.on_command("loaded_accounts", description="Shows loaded accounts")
async def get_loaded_accounts(client, message):
    accounts = []

    async def get_account_info(account, channel: list):
        channel.append("account " + (await account.info).username)

    await client.account.manager.async_foreach(get_account_info, accounts)

    await message.reply(
        text="Accounts loaded:\n"
        + "\n".join(f"- {account}" for account in accounts)
    )


@command_manager.on_command("bot", owner_only=True, description="Shows bot information")
async def info(client: ExtendedClient, message: types.Message):
    accounts = []

    async def get_account_info(account: Account, channel: list):
        account_info = await account.info
        full_name = account_info.first_name + (" " + account_info.last_name if account_info.last_name else "")
        channel.append(f"{full_name}(@{account_info.username}:{account_info.id})")

    await client.account.manager.async_foreach(get_account_info, accounts)

    top_used_commands = sorted(
        command_manager.parent.get_statistic(),
        key=lambda record: record["call_count"],
        reverse=True
    )[:5]

    top_used_commands_text = ', '.join(
        f"{record['command'].body}({record['call_count']})" for record in top_used_commands
    )

    await message.edit(
        text="KuyuGenesis userbot:\n"
             f"    Version: {config.version}\n"
             f"    Name: {config.name}\n"
             f"    Owners: {', '.join(accounts)}\n"
             f"    Loaded addons: {len(addons_loader.system.get_enabled_addons())}\n"
             f"    Included command managers: {len(get_all_command_managers())}\n"
             f"    Included event managers: {len(get_all_event_managers())}\n"
             f"    Total commands call count: {command_manager.parent.get_total_call_count()}\n"
             f"    Top-5 used commands: {top_used_commands_text}"
    )


@command_manager.on_command("commands", description="Shows addon registered commands")
async def get_commands(_: ExtendedClient, message: types.Message):

    # noinspection PyUnresolvedReferences
    arguments = message.arguments

    if not len(arguments):
        return await message.edit(
            message.text + "\n\nPlease, type addon name after the command"
        )

    try:
        addon_command_manager = addons_loader.system.get_addon_command_manager(message.text.split(maxsplit=1)[1])
    except ValueError:
        return await message.edit(
            message.text + "\n\nAddon not found"
        )
    except AttributeError:
        return await message.edit(
            message.text + "\n\nAddon hasn't command manager"
        )

    def describe_command(command: Command) -> str:
        return (
            f"<b>{command.body}</b>:\n"
            f"    <b>Prefixes</b>: {', '.join(command.prefixes)}\n"
            f"    <b>Description</b>: {command.description or 'undescribed'}\n"
            f"    <b>Arguments</b>: {', '.join(command.arguments) if len(command.arguments) else 'not required'}\n"
            f"    <b>Only owner-usable</b>: {command.owner_only}\n"
            f"    <b>Is enabled</b>: {command.enabled}"
        )

    def describe_manager(manager: CommandManager) -> str:
        return (
            f"From <b>{manager.addon.meta.name if manager.addon != manager.NO_ADDON else 'Built-in'}</b>:\n"
            + "\n\n".join(
                "    " + describe_command(command).replace("\n", "\n    ")
                for command in manager.get_registered_commands()
            )
        )

    await message.edit_text(
        "All commands:\n"
        + describe_manager(addon_command_manager)
    )


@command_manager.on_command(
    "addons",
    description="Shows available addons",
    arguments=("addon status(loaded|enabled|disabled|all)",)
)
async def get_addons(_: ExtendedClient, message: types.Message):

    # noinspection PyUnresolvedReferences
    arguments = message.arguments

    status = "loaded"

    if len(arguments):
        status = arguments[0][0].lower()

    if status not in ("loaded", "enabled", "disabled", "all"):
        return await message.edit(
            message.text + f"\n\nNot allowed addon status: {status}"
        )

    match status:
        case "loaded":
            addons = list(addons_loader.LOADED_ADDONS)
        case "enabled":
            addons = addons_loader.system.get_enabled_addons()
        case "disabled":
            addons = addons_loader.system.get_disabled_addons()
        case "all":
            addons = addons_loader.system.get_all_addons()
        case _:
            return await message.edit(
                message.text + f"\n\nUnsupported status value: {status}"
            )

    addons.sort(key=lambda addon: (addon.meta.author, addon.meta.name))

    text = f"{status.capitalize()} addons:\n"

    def addon_status(addon):
        return "🟢" if addon.meta.status == "enabled" else "🔴"

    text += "\n\n".join(
        f"{addon_status(addon)}{addon.meta.name} v{addon.meta.version} by {addon.meta.author}\n"
        f"Details: <code>.addon {addon.meta.name}</code>"
        for addon in addons
    )

    await message.edit(text)


def describe_addon(addon: Addon) -> str:
    if addon.meta.status == "enabled":
        has_command_manager = hasattr(addon.module, "get_command_manager")

        text = (
                f"Name: \u200d{addon.meta.name}\u200c\n"
                f"Status: {addon.meta.status}\n"
                f"Version: {addon.meta.version}\n"
                f"Description: {addon.meta.description}\n\n"
                f"Has command manager: {'yes' if has_command_manager else 'no'}\n"
                f"Has event manager: {'yes' if hasattr(addon.module, 'get_event_manager') else 'no'}\n"
                f"Dependencies:\n  "
                + (
                    "\n  ".join(
                        f"{lib['name']}=={lib['version']}"
                        for lib in addon.meta.requirements
                    ) if addon.meta.requirements else "  Hasn't dependencies"
                )
        )
    else:
        text = (
                f"Name: \u200d{addon.meta.name}\u200c\n"
                f"Status: {addon.meta.status}\n"
                f"Version: {addon.meta.version}\n"
                f"Description: {addon.meta.description}\n\n"
                f"Has command manager: Cannot define on disabled addons\n"
                f"Has event manager: Cannot define on disabled addons\n"
                f"Dependencies:\n  "
                + (
                    "\n  ".join(
                        f"{lib['name']}=={lib['version']}"
                        for lib in addon.meta.requirements
                    ) if addon.meta.requirements else "  Hasn't dependencies"
                )
        )

    return text


@command_manager.on_command("addon", description="Shows information about addon", arguments=("addon name",))
async def get_addon_info(_: ExtendedClient, message: types.Message):
    # noinspection PyUnresolvedReferences
    arguments = message.arguments

    if not len(arguments):
        return await message.edit(
            message.text + "\n\nType addon name, to see details"
        )

    addon_name = " ".join(arguments[0])

    addon = addons_loader.system.get_addon_by_name(addon_name)

    if addon_name == "MAIN ADDON":
        addon = this_addon

    text = describe_addon(addon)

    text += "\n\nType +(to enable addon)/-(to disable addon) in reply to this message"

    await message.edit(text)


addon_name_regexp = re.compile("Name: \u200d(.+)\u200c\n")


@event_manager.on_message(
    F.message.text.in_({"+", "-"}) & F.message.reply_to_message.text.func(addon_name_regexp.match)
)
async def toggle_addon(event: NewMessageEvent):
    addon_name = addon_name_regexp.match(event.message.reply_to_message.text).group(1)

    addon = addons_loader.system.get_addon_by_name(addon_name)

    if not addon:
        return await event.message.edit_text(
            text=event.message.text + "\n\nAddon not found"
        )

    match event.message.text:
        case "+":
            addons_loader.enable_addon(addon, True)
        case "-":
            addons_loader.disable_addon(addon)

    text = describe_addon(addon)

    text += "\n\nType +(to enable addon)/-(to disable addon) in reply to this message"

    await event.message.reply_to_message.edit(
        text
    )

    await event.message.delete()

