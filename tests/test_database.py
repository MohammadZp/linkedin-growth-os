from __future__ import annotations

from app.database.session import ensure_sqlite_parent_dir


def test_ensure_sqlite_parent_dir_creates_nested_dir(tmp_path) -> None:
    db_file = tmp_path / "nested" / "sub" / "app.db"
    url = f"sqlite:///{db_file}"
    ensure_sqlite_parent_dir(url)
    assert db_file.parent.is_dir()


def test_ensure_sqlite_parent_dir_ignores_memory(tmp_path) -> None:
    ensure_sqlite_parent_dir("sqlite:///:memory:")
    ensure_sqlite_parent_dir("sqlite://")
    # No exception raised and nothing created.
    assert list(tmp_path.iterdir()) == []
