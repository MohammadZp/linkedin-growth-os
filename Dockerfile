# LinkedIn Growth OS — production image
#
# The bot uses Telegram long polling, so it must run as a single
# instance. It exposes no inbound ports.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies (no dev extras) from the pinned project metadata.
# Copying these before the source lets Docker cache the dependency layer.
COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
RUN pip install --no-cache-dir .

# Non-root user, plus a writable data directory for SQLite. A named volume is
# mounted at /app/data at runtime; Docker copies this directory's ownership into
# the empty volume on first use, so the non-root user can write to it. The app
# dir itself is owned by the user so scripts/backup.py can write under /app.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "app.main"]
