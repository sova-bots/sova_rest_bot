from datetime import datetime

import config as cf


def is_working_day() -> bool:
    now = datetime.now(tz=cf.TIMEZONE)
    today = now.date()
    weekday = today.weekday()
    return weekday in [0, 1, 2, 3, 4]


if __name__ == '__main__':
    print(is_working_day())
