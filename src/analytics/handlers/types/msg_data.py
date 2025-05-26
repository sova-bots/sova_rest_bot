from dataclasses import dataclass

from aiogram.types import Message
from aiogram.fsm.context import FSMContext


@dataclass
class MsgData:
    msg: Message
    state: FSMContext
    tgid: int | None = None
