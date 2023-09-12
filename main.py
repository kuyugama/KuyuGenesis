import asyncio
from logging import INFO

from pyrogram import Client, filters, errors
from kgemng import EventManager, CommandManager
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from colorama import Fore

from core import MainAddon
from core import exceptions, Account, AccountManager
from core.addons_loader import load_main_addon, system, load_addons
from core import addons_loader
from core.database.init import init_engine
from core.logs import get_logger, wrap_into_color

import config

logger = get_logger("StartupService", INFO)

if __name__ != "__main__":
    raise exceptions.StartupError(
        "This python code file must be opened via interpreter"
    )


def error_handler(exception, context):
    error_handler_logger = get_logger("MainErrorHandler")
    if isinstance(exception, errors.FloodWait):
        return

    error_handler_logger.warning(f"Error occurred {exception}. Context: {context}")


async def main():

    logger.info("{name} starting...".format(name=wrap_into_color(config.name, color=Fore.YELLOW)))

    account_manager = AccountManager()

    addons_loader.system.set_main_addon(MainAddon.this_addon)

    await init_engine()

    command_manager = CommandManager(CommandManager.NO_ADDON, True)

    command_manager.set_error_handler(error_handler)

    event_manager = EventManager(EventManager.NO_ADDON, True)

    event_manager.set_error_handler(error_handler)

    addons_loader.init(command_manager, event_manager)

    for index in range(1, config.accounts_count + 1):
        name = "account"
        if index > 1:
            name += f"-{index}"

        name = str(config.sessions_root / name)

        client = Client(
            name,
            api_id=config.api_id,
            api_hash=config.api_hash,
            device_model=config.name,
            app_version=config.version,
            sleep_threshold=0,
        )

        account = Account(client)

        account_manager.add_account(account)

        account.manager = account_manager

        client.account = account

        client.add_handler(MessageHandler(command_manager.execute, filters.text))
        client.add_handler(RawUpdateHandler(event_manager.execute))

    load_main_addon()
    load_addons(*system.get_enabled_addons())

    for account in account_manager.get_accounts():
        await account.client.start()
        account_info = await account.resolve_info()
        logger.info(
            "Account [ {name} ] has been loaded!".format(
                name=wrap_into_color(
                    f"{account_info.first_name}"
                    + (" " + account_info.last_name if account_info.last_name else ""),
                    color=Fore.YELLOW
                )
            )
        )

    logger.info("{name} started and waiting for updates!".format(name=wrap_into_color(config.name, color=Fore.YELLOW)))
    while 1:
        await asyncio.sleep(1800)


asyncio.run(main())
