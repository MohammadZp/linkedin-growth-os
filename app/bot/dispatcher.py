from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import analytics, common, content, ideas, leads, menu, review, tasks
from app.bot.middlewares.access import AccessControlMiddleware
from app.config import Settings


def build_dispatcher(settings: Settings) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(AccessControlMiddleware(settings.telegram_allowed_user_id))
    dp.include_routers(
        common.router,
        content.router,
        ideas.router,
        tasks.router,
        analytics.router,
        leads.router,
        review.router,
        menu.router,
    )
    return dp
