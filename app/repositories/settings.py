from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import AppSetting


class SettingsRepository:
    """Key/value store for runtime-tunable settings (e.g. pillar proportions)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.session.get(AppSetting, key)
        return row.value if row is not None else default

    def set(self, key: str, value: str) -> None:
        row = self.session.get(AppSetting, key)
        if row is None:
            self.session.add(AppSetting(key=key, value=value))
        else:
            row.value = value

    def all(self) -> dict[str, str]:
        rows = self.session.query(AppSetting).all()
        return {row.key: row.value for row in rows if row.value is not None}
