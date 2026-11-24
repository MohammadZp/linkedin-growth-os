from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramRetryAfter

from app.bot.dispatcher import build_dispatcher
from app.config import get_settings
from app.database import init_db

logger = logging.getLogger(__name__)


async def _call_with_retry(
    call: Callable[[], Awaitable[object]],
    *,
    attempts: int = 10,
    label: str = "Telegram call",
) -> object:
    """Run an async Telegram call, waiting out flood control (``TelegramRetryAfter``).

    aiogram's polling loop already retries ``getUpdates`` via its backoff config, but
    the one-shot startup call (``getMe``) is not wrapped. A rate-limited bot would
    crash on it and the restart policy would re-hammer the API; instead we wait out
    ``retry_after`` here so a single process rides out the throttle.
    """
    for attempt in range(1, attempts + 1):
        try:
            return await call()
        except TelegramRetryAfter as exc:
            if attempt == attempts:
                raise
            logger.warning(
                "%s rate-limited (attempt %s/%s); waiting %ss",
                label,
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
    # Warm bot.me() once so start_polling's internal getMe hits the cache
    # instead of calling Telegram directly and tripping flood control.
    await _call_with_retry(bot.me, label="getMe")
    logger.info("Bot started. Polling for updates...")
    await dp.start_polling(bot)


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
