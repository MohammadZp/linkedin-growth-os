# LinkedIn Growth OS

A Telegram bot that turns a personal LinkedIn growth strategy into daily tasks, tracks
execution, measures outcomes, and recommends improvements — built for a software engineer
with a full-time job and ~1–2 h/day to spend on LinkedIn.

The bot is a **personal assistant**: it never publishes to LinkedIn, never messages
LinkedIn contacts, and never scrapes LinkedIn. You record outcomes manually, and the bot
helps you stay consistent and honest about what is actually working.

## What it does

- **Daily tasks** — today's list, overdue items, mark complete, next scheduled publication,
  and a daily briefing at a configurable time.
- **Content pipeline** — ideas → researching → drafting → review → scheduled → published →
  archived, with duplicate-schedule protection.
- **Idea management** — inbox/shortlisted/selected/rejected with a transparent,
  configurable prioritisation score.
- **Analytics** — manual recording of impressions, reactions, comments, reposts, profile
  views, connection requests, qualified conversations and leads; weekly summaries that
  compare posts and content pillars and frame impressions as reach, not success.
- **Lightweight CRM** — contacts with stage, opportunity status, business need, follow-up
  dates and notes; AI-drafted outreach messages (explicit approval required, never sent
  automatically).
- **Weekly strategy review** — nine sections that separate observations from hypotheses
  and avoid strong claims on small samples.
- **Optional LLM** — suggest ideas, draft hooks/angles/scripts, summarise stats, draft
  messages and propose experiments. The app is fully usable without any LLM configured.

All bot messages are in **Persian**; code, identifiers, logs and docs are in **English**.

## Stack

Python 3.12+, aiogram 3.x, SQLAlchemy 2.x (SQLite), APScheduler, pydantic-settings,
pytest, ruff. Versions are pinned in `pyproject.toml`.

## Quick start

```bash
# 1. Create and activate a virtualenv
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -e ".[dev]"
# macOS / Linux
.venv/bin/python -m pip install -e ".[dev]"

# 2. Configure
cp .env.example .env      # then fill in real values (see Configuration below)

# 3. Run
.venv\Scripts\python -m app.main     # or: .venv/bin/python -m app.main
```

## Configuration

Copy `.env.example` to `.env` and fill in real values. Never commit `.env`.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | yes | — | Bot token from @BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | yes | — | Telegram user id of the only allowed user |
| `DATABASE_URL` | no | `sqlite:///./data/linkedin_growth.db` | SQLAlchemy URL |
| `TIMEZONE` | no | `Asia/Tehran` | IANA timezone for scheduling/formatting |
| `DAILY_BRIEFING_TIME` | no | `08:00` | Daily briefing time, 24h `HH:MM` |
| `WEEKLY_REVIEW_DAY` | no | `4` | 0=Monday … 6=Sunday |
| `WEEKLY_REVIEW_TIME` | no | `18:00` | Weekly review time, 24h `HH:MM` |
| `PUBLISHING_TARGET_PER_WEEK` | no | `3` | Weekly publishing goal |
| `MAX_DAILY_TASKS` | no | `3` | Daily task cap |
| `DEFAULT_CONTENT_LANGUAGE` | no | `en` | Default content language |
| `CONTENT_PILLARS` | no | see `.env.example` | Pillar proportions (JSON) |
| `IDEA_WEIGHTS` | no | see `.env.example` | Idea score weights (JSON) |
| `AI_PROVIDER` | no | — | `anthropic` or `openai` (empty disables LLM) |
| `AI_API_KEY` | no | — | Provider API key |
| `AI_MODEL` | no | `claude-opus-5-5` | Model override |
| `AI_BASE_URL` | no | — | Override the provider API base URL |

## Commands

| Command | Purpose |
| --- | --- |
| `/start` | Greet and register the user |
| `/help` | Usage overview |
| `/today` | Today's tasks, overdue, next publication |
| `/week` | Upcoming scheduled publications |
| `/ideas` | Manage and score content ideas |
| `/content` | Manage the content pipeline |
| `/stats` | Record and review performance |
| `/leads` | Manage contacts and follow-ups |
| `/settings` | Show current configuration |
| `/review` | Weekly strategy review (9 sections) |
| `/cancel` | Abort the current multi-step flow |

Only `TELEGRAM_ALLOWED_USER_ID` can use the bot. A global access-control middleware
rejects every other user's updates.

## Layout

```
app/
  main.py            # entrypoint
  config.py          # pydantic-settings configuration
  domain/            # enums and pure domain types
  database/          # SQLAlchemy models, session, base
  repositories/      # data access
  services/          # business rules (content, tasks, analytics, contacts, review, …)
  bot/               # aiogram handlers, keyboards, texts, middlewares
  scheduler/         # APScheduler jobs (briefing + weekly review)
  ai/                # optional LLM provider abstraction + prompts
scripts/
  backup.py          # database backup / JSON export
tests/
```

## Architecture notes

- **Time** is stored in UTC and converted to the configured timezone only at the
  boundary (scheduler, formatting). Dates are naive.
- **Enums** live in `app/domain/enums.py` and are stored as their string `.value`.
- **Repositories** wrap the SQLAlchemy `Session`; business rules live in `app/services`,
  never in handlers.
- **Scheduler** uses APScheduler's `AsyncIOScheduler` with fixed job ids,
  `replace_existing=True`, `coalesce=True` and `max_instances=1`, plus idempotency
  markers in the `app_settings` table so briefings/reviews are not double-sent.
- **LLM** is behind a provider abstraction (`app/ai/providers.py`). Prompts live in
  `app/ai/prompts.py`, forbid fabricating facts and require plain text (no markdown).

## Security & privacy

- Secrets come from environment variables / `.env`; `.env` and `data/` are gitignored.
- Tokens, keys and personal data are never logged.
- Access is restricted to `TELEGRAM_ALLOWED_USER_ID` via an outer middleware.
- URLs and free-text inputs are validated before persisting.
- No browser automation, no unofficial LinkedIn APIs, no scraping. The bot never
  publishes to LinkedIn or sends LinkedIn messages.

## Backup & export

The SQLite database lives at `data/linkedin_growth.db`. Back it up any time (safe while
the bot is running — it uses SQLite's online backup API for a consistent snapshot):

```bash
.venv\Scripts\python scripts\backup.py backup          # copy to backups/*.db
.venv\Scripts\python scripts\backup.py export-json     # dump all tables to JSON
```

`backups/` is gitignored. Schedule a periodic backup (e.g. daily) with your OS scheduler
for production use.

## Development

```bash
# Windows
.venv\Scripts\ruff check .          # lint
.venv\Scripts\ruff format .         # format
.venv\Scripts\python -m pytest      # test
```

Ruff config and pytest options are in `pyproject.toml`. Tests run against an in-memory
SQLite database and cover services, repositories, time conversion, scoring, scheduler
idempotency, the LLM abstraction and a bot smoke test (all routers wired).
"# linkedin-growth-os" 
