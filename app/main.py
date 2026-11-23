from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramRetryAfter

from app.bot.dispatcher import build_dispatcher
from app.config import get_settings
from app.database import init_db
from app.scheduler.manager import build_scheduler

logger = logging.getLogger(__name__)


async def _reset_webhook(bot: Bot, *, attempts: int = 5) -> None:
    """Drop pending updates, waiting out Telegram's rate limit on ``delete_webhook``.

    ``DeleteWebhook`` is rate-limited aggressively by Telegram. When the container
    restarts in a crash loop, each start re-hits it and keeps tripping the limit;
    instead we honour ``retry_after`` and retry, and if the limit never clears we
    continue to polling anyway (this bot sets no webhook).
    """
    for attempt in range(1, attempts + 1):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            return
        except TelegramRetryAfter as exc:
            if attempt == attempts:
                logger.warning(
                    "delete_webhook still rate-limited after %s attempts; continuing",
                    attempts,
                )
                return
            logger.warning(
                "delete_webhook rate-limited (attempt %s/%s); waiting %ss",
                attempt,
                attempts,
                exc.retry_after,
            )
            await asyncio.sleep(exc.retry_after)


async def run_bot() -> None:
    settings = get_settings()
    init_db()
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill in real values."
        )
    if not settings.telegram_allowed_user_id:
        raise RuntimeError(
            "TELEGRAM_ALLOWED_USER_ID is not set. Only the configured user may use this bot."
        )

    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties())
    dp: Dispatcher = build_dispatcher(settings)
    scheduler = build_scheduler(bot, settings)
    scheduler.start()
    try:
        await _reset_webhook(bot)
        logger.info("Bot started. Polling for updates...")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")
    except RuntimeError as exc:
        logger.error(exc)


if __name__ == "__main__":
    main()
