import config as cf
from datetime import datetime
from colorama import Fore, Style
from colorama import init as colorama_init


def init() -> None:
    colorama_init()


class Defaults:
    DT_FORMAT: str = '%d.%m.%Y %H:%M:%S'
    DEBUG = True


class LogMessageType:
    INFO: str = 'INFO'
    DEBUG: str = 'DEBUG'
    WARNING: str = 'WARNING'
    ERROR: str = 'ERROR'


def info(message: str, color: Fore = Fore.GREEN) -> None: # type: ignore
    msg(LogMessageType.INFO, message, color)


def debug(message: str, color: Fore = Fore.MAGENTA) -> None: # type: ignore
    if Defaults.DEBUG:
        msg(LogMessageType.DEBUG, message, color)


def msg(msg_type: str, message: str, color: Fore = Fore.CYAN) -> None: # type: ignore
    now = datetime.now(tz=cf.TIMEZONE)
    text = f'{Style.DIM}{Fore.WHITE}{now.strftime(Defaults.DT_FORMAT)} {Style.NORMAL}{color}[{msg_type}] {Fore.RESET}{message}{Style.RESET_ALL}'
    print(text)
