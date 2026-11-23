from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import session_scope
from app.repositories.settings import SettingsRepository
from app.scheduler.briefing import build_daily_briefing
from app.services.review import build_weekly_review
from app.services.time import local_date

logger = logging.getLogger(__name__)


def _review_builder(session: Session, settings: Settings) -> str:
    text = build_weekly_review(session, settings)
    return text if len(text) <= 4000 else text[:4000]


def _parse_hhmm(hhmm: str) -> tuple[int, int]:
    hour, minute = hhmm.split(":", 1)
    return int(hour), int(minute)


def build_scheduler(bot: Bot, settings: Settings) -> AsyncIOScheduler:
    """Create and configure the scheduler. Jobs use fixed ids + replace_existing so a
    repeated registration cannot produce duplicate briefings."""
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    hour, minute = _parse_hhmm(settings.daily_briefing_time)
    scheduler.add_job(
        daily_briefing_job,
        CronTrigger(hour=hour, minute=minute, timezone=settings.timezone),
        args=[bot, settings],
        id="daily_briefing",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    hour, minute = _parse_hhmm(settings.weekly_review_time)
    scheduler.add_job(
        weekly_summary_job,
        CronTrigger(
            day_of_week=settings.weekly_review_day,
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
        ),
        args=[bot, settings],
        id="weekly_summary",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    return scheduler


async def daily_briefing_job(bot: Bot, settings: Settings) -> None:
    await _send_scheduled(
        bot, settings, "last_daily_briefing", local_date().isoformat(), build_daily_briefing
    )


async def weekly_summary_job(bot: Bot, settings: Settings) -> None:
    week_start = local_date() - timedelta(days=local_date().weekday())
    await _send_scheduled(
        bot, settings, "last_weekly_summary", week_start.isoformat(), _review_builder
    )


async def _send_scheduled(
    bot: Bot,
    settings: Settings,
    key: str,
    marker: str,
    builder: Callable[[Session, Settings], str],
) -> None:
    try:
        with session_scope() as session:
            if SettingsRepository(session).get(key) == marker:
                logger.info("Skipping %s: already sent for %s", key, marker)
                return
            text = builder(session, settings)
        await _send_with_retry(bot, settings.telegram_allowed_user_id, text)
        with session_scope() as session:
            SettingsRepository(session).set(key, marker)
    except Exception:
        logger.exception("Failed to send scheduled message %s", key)


async def _send_with_retry(bot: Bot, chat_id: int, text: str, attempts: int = 3) -> None:
    delay = 1.0
    for attempt in range(attempts):
        try:
            await bot.send_message(chat_id, text)
            return
        except TelegramRetryAfter as exc:
            logger.warning("Telegram rate limited; retrying in %ss", exc.retry_after)
            await asyncio.sleep(exc.retry_after)
        except Exception as exc:
            logger.warning("send_message failed (attempt %s/%s): %s", attempt + 1, attempts, exc)
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(delay)
            delay *= 2
