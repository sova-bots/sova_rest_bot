from aiogram.fsm.state import State, StatesGroup


local_report_types = {
    "losses/product": "Закупки потери ФАКТ",
}

local_periods = {
    "last-day": "Вчерашний день",
    "this-week": "Текущая неделя",
    "this-month": "Текущий месяц",
    "last-week": "Прошлая неделя",
    "last-month": "Прошлый месяц",
}

class FSMLosses(StatesGroup):
    ask_report = State()
    ask_period = State()