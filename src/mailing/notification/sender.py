from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from datetime import datetime, timedelta

from ..data.notification.notification_google_sheets_worker import notification_gsworker, MessageColumn
from .calendar import is_working_day

from src.util.log import logger
import config as cf


async def test_job() -> None:
    print('4len')


class NotificationSender:
    scheduler: AsyncIOScheduler
    bot: Bot

    def __init__(self, bot: Bot) -> None:
        self.scheduler = AsyncIOScheduler(timezone=cf.TIMEZONE, job_defaults={'misfire_grace_time': None})
        self.bot = bot

    async def notify(self, message_col: int) -> None:
        for user_id, message in notification_gsworker.get_messages(message_col):
            await self.bot.send_message(user_id, message)

    async def daily_job(self) -> None:
        await self.notify(MessageColumn.DAY)
        logger.info('Sent messages for this day')

    async def weekly_job(self) -> None:
        await self.notify(MessageColumn.WEEK)
        logger.info('Sent messages for this week')

    async def monthly_notify(self) -> None:
        await self.notify(MessageColumn.MONTH)
        logger.info('Sent messages for this month')

    async def monthly_job(self) -> None:
        if is_working_day():
            await self.monthly_notify()
            return
        self.scheduler.add_job(self.monthly_job, 'interval', day=1)
        logger.info('wait until work')

    def start(self) -> None:
        pattern = '%H:%M'
        day_dt = (datetime.now(tz=cf.TIMEZONE) + timedelta(seconds=5)).time()  #datetime.strptime(cf.SENDING_TIME['DAY'], pattern).time()
        week_dt = datetime.strptime(cf.SENDING_TIME['WEEK'], pattern).time()
        month_dt = datetime.strptime(cf.SENDING_TIME['MONTH'], pattern).time()

        self.scheduler.add_job(self.daily_job, 'cron', day_of_week=cf.WORKING_DAYS, hour=day_dt.hour, minute=day_dt.minute, second=day_dt.second)
        self.scheduler.add_job(self.weekly_job, 'cron', day_of_week=cf.WEEKLY_DAY, hour=week_dt.hour, minute=week_dt.minute)
        self.scheduler.add_job(self.monthly_job, 'cron', day=cf.MONTHLY_DAY, hour=month_dt.hour, minute=month_dt.minute)

        self.scheduler.start()

    def stop(self) -> None:
        self.scheduler.shutdown()
