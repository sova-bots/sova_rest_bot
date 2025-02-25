import config as cf
from datetime import datetime
from colorama import Fore, Style
from colorama import init as colorama_init


def init() -> None:
    colorama_init()


class Defaults:
    DT_FORMAT: str = '%d.%m.%Y %H:%M:%S'


class LogMessageType:
    INFO: str = 'INFO'
    WARNING: str = 'WARNING'
    ERROR: str = 'ERROR'


def info(message: str, color: Fore = Fore.GREEN) -> None:
    msg(LogMessageType.INFO, message, color)


def msg(msg_type: str, message: str, color: Fore = Fore.CYAN) -> None:
    now = datetime.now(tz=cf.TIMEZONE)
    text = f'{Style.DIM}{Fore.WHITE}{now.strftime(Defaults.DT_FORMAT)} {Style.NORMAL}{color}[{msg_type}] {Fore.RESET}{message}{Style.RESET_ALL}'
    print(text)
