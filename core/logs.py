import logging
from logging import getLogger, Formatter, StreamHandler, WARNING

from colorama import init, Fore, Style, Back

from config import name

init()


MESSAGE_COLOR = Fore.LIGHTGREEN_EX
LOGGER_NAME_COLOR = Fore.CYAN
TIME_COLOR = Fore.GREEN

level_colors = {
    logging.DEBUG: Fore.YELLOW,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.LIGHTRED_EX,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Back.WHITE
}


class LevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self._level


def stream_handler(level: int):
    level_color = level_colors[level]

    handler = StreamHandler()
    handler.setFormatter(
        Formatter(
            f"{level_color}%(levelname)s{Style.RESET_ALL} "
            f"{Fore.WHITE}[{TIME_COLOR}%(asctime)s{Fore.WHITE}] {Style.RESET_ALL}%(name)s\n"
            f"    {MESSAGE_COLOR}%(message)s{Style.RESET_ALL}\n"
        )
    )

    handler.setLevel(level)
    handler.addFilter(LevelFilter(level))

    return handler


def get_logger(logger_name: str, log_level=WARNING):
    logger_name = (
        f"{LOGGER_NAME_COLOR}KuyuGenesis{Style.RESET_ALL}"
        f"|{LOGGER_NAME_COLOR}{name}{Style.RESET_ALL}"
        f"|{LOGGER_NAME_COLOR}{logger_name}{Style.RESET_ALL}"
    )
    logger = getLogger(logger_name)

    logger.setLevel(level=log_level)
    logger.addHandler(stream_handler(logging.DEBUG))
    logger.addHandler(stream_handler(logging.INFO))
    logger.addHandler(stream_handler(logging.WARNING))
    logger.addHandler(stream_handler(logging.ERROR))
    logger.addHandler(stream_handler(logging.CRITICAL))

    return logger


def wrap_into_color(*args: str, color=Fore.WHITE, return_to_color=MESSAGE_COLOR):
    return color + "".join(args) + return_to_color
