from __future__ import annotations

from aiogram import Bot
from app.config import Settings
from app.repositories.settings import SettingsRepository
from app.scheduler.manager import _parse_hhmm, build_scheduler
from sqlalchemy.orm import Session

DUMMY_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"


def test_parse_hhmm() -> None:
    assert _parse_hhmm("08:00") == (8, 0)
    assert _parse_hhmm("18:30") == (18, 30)


def test_build_scheduler_registers_both_jobs_once() -> None:
    bot = Bot(token=DUMMY_TOKEN)
    scheduler = build_scheduler(bot, Settings(_env_file=None))
    job_ids = [job.id for job in scheduler.get_jobs()]
    assert job_ids.count("daily_briefing") == 1
    assert job_ids.count("weekly_summary") == 1


def test_settings_repository_sentinel(session: Session) -> None:
    repo = SettingsRepository(session)
    assert repo.get("last_daily_briefing") is None
    repo.set("last_daily_briefing", "2026-11-23")
    session.commit()
    assert repo.get("last_daily_briefing") == "2026-11-23"
