# LinkedIn Growth OS

Telegram bot for managing personal LinkedIn growth: content, ideas, daily tasks,
performance analytics, and a lightweight CRM.

## Stack

Python 3.12+, aiogram 3.x, SQLAlchemy 2.x (SQLite), pydantic-settings,
pytest, ruff.

## Commands (Windows)

- Create venv: `python -m venv .venv`
- Install: `.venv\Scripts\python -m pip install -e ".[dev]"`
- Lint: `.venv\Scripts\ruff check .`
- Format: `.venv\Scripts\ruff format .`
- Test: `.venv\Scripts\python -m pytest`

## Conventions

- **Time:** all datetimes are stored in UTC; convert to the configured timezone
  (default `Asia/Tehran`) only at the formatting boundary. Dates are naive.
- **Language:** bot user-facing messages are Persian; code, identifiers, logs, docs are English.
- **Enums** live in `app/domain/enums.py`; SQLAlchemy models in `app/database/models.py`.
  Enums are stored as their string `.value`.
- **Access:** single authorized user (`TELEGRAM_ALLOWED_USER_ID`).
- **Repositories** wrap `Session`; business rules belong in `app/services`, not handlers.
- No LinkedIn automation/scraping. The bot never publishes or messages LinkedIn directly.
