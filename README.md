# LinkedIn Growth OS

A Telegram bot that turns a personal LinkedIn growth strategy into daily tasks, tracks
execution, measures outcomes, and recommends improvements — built for a software engineer
with a full-time job and ~1–2 h/day to spend on LinkedIn.

The bot is a **personal assistant**: it never publishes to LinkedIn, never messages
LinkedIn contacts, and never scrapes LinkedIn. You record outcomes manually, and the bot
helps you stay consistent and honest about what is actually working.

## What it does

- **Daily tasks** — today's list, overdue items, mark complete, next scheduled publication,
  and an on-demand daily briefing (`/briefing`).
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

Python 3.12+, aiogram 3.x, SQLAlchemy 2.x (SQLite), pydantic-settings,
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
| `TIMEZONE` | no | `Asia/Tehran` | IANA timezone for date formatting |
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
| `/briefing` | Daily briefing (today's priorities, overdue, next publication) |
| `/today` | Today's tasks (toggle complete / delete) |
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
  ai/                # optional LLM provider abstraction + prompts
scripts/
  backup.py          # database backup / JSON export
tests/
```

## Architecture notes

- **Time** is stored in UTC and converted to the configured timezone only at the
  formatting boundary. Dates are naive.
- **Enums** live in `app/domain/enums.py` and are stored as their string `.value`.
- **Repositories** wrap the SQLAlchemy `Session`; business rules live in `app/services`,
  never in handlers.
- **No background scheduler** — the daily briefing and weekly review are triggered
  manually via `/briefing` and `/review`.
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

## Deployment (Docker Compose)

Run the bot in a single container on a Linux VPS (Ubuntu 22.04/24.04) with Docker
Compose v2. The bot uses Telegram **long polling**, so it must stay a **single
instance** — do not scale replicas.

### Prerequisites

- Docker Engine and Docker Compose v2 on the VPS.
- The VPS can reach `https://api.telegram.org`.

### Clone or update

```bash
git clone <your-repo-url> linkedin-growth-os
cd linkedin-growth-os
# on an existing checkout, pull the latest instead:
git pull
```

### Create the deployment `.env`

```bash
cp .env.example .env
nano .env   # fill in TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID
```

`.env` is gitignored — never commit it. The container loads it via Compose `env_file`.

### Start

```bash
docker compose up -d --build
```

### Logs

```bash
docker compose logs -f bot
```

### Restart / stop

```bash
docker compose restart bot     # restart in place
docker compose stop            # stop the container
docker compose down            # stop and remove the container (keeps the data volume)
```

### Update after a Git change

```bash
git pull
docker compose up -d --build
```

### Back up / restore the SQLite database

The database lives in the named volume `data`, mounted at `/app/data` inside the
container, so it survives container recreation.

```bash
# Backup (safe while running — uses SQLite's online backup API):
docker compose exec bot python scripts/backup.py backup
docker compose cp bot:/app/backups/linkedin_growth_<timestamp>.db ./backup.db
# Portable JSON export (alternative):
docker compose exec bot python scripts/backup.py export-json
docker compose cp bot:/app/backups/linkedin_growth_<timestamp>.json ./export.json

# Restore (stop the bot first):
docker compose stop bot
docker compose cp ./backup.db bot:/app/data/linkedin_growth.db
docker compose start bot
```

### Troubleshooting

- **Invalid token / 401 Unauthorized** — check `TELEGRAM_BOT_TOKEN` in `.env`, then
  `docker compose restart bot`.
- **Bot ignores your messages** — `TELEGRAM_ALLOWED_USER_ID` must be your numeric
  Telegram id; confirm it and restart.
- **Can't reach Telegram** — from the VPS: `curl -sS https://api.telegram.org`; if it
  fails, the VPS has no outbound HTTPS access to Telegram.
- **Time is wrong** — set `TIMEZONE` (IANA name) in `.env`; the `tzdata` package is
  already installed in the image.

> There is no container health check: a generic HTTP probe cannot verify that Telegram
> polling is healthy, so watch `docker compose logs -f bot` instead.

## Development

```bash
# Windows
.venv\Scripts\ruff check .          # lint
.venv\Scripts\ruff format .         # format
.venv\Scripts\python -m pytest      # test
```

Ruff config and pytest options are in `pyproject.toml`. Tests run against an in-memory
SQLite database and cover services, repositories, time conversion, scoring, the LLM
abstraction and a bot smoke test (all routers wired).
