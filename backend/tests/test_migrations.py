import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_migrations_create_foreign_keys_and_can_be_reapplied(tmp_path: Path) -> None:
    database = tmp_path / "migration.db"
    environment = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{database.as_posix()}"}

    results = []
    for action, target in [("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")]:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", action, target],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(result)
    parity = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    for result in results:
        assert result.returncode == 0, result.stderr
    with sqlite3.connect(database) as connection:
        assert connection.execute("select version_num from alembic_version").fetchone() == ("0003",)
        assert len(connection.execute("pragma foreign_key_list(tasks)").fetchall()) == 3
    assert parity.returncode == 0, parity.stdout + parity.stderr


def test_collaboration_migration_preserves_legacy_tasks_and_weeks(tmp_path: Path) -> None:
    database = tmp_path / "legacy.db"
    environment = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{database.as_posix()}"}

    def migrate(target: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", target],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    migrate("0001")
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO departments VALUES (1, 'Demo', 'Leader')")
        connection.execute("INSERT INTO users VALUES (1, 'Demo', '[\"office\"]', '[1]')")
        connection.execute(
            "INSERT INTO tasks VALUES (1, 'Legacy task', '', 1, 1, 1, "
            "'2026-11-08', 'personal', 'normal', 'in_progress')"
        )
        connection.execute("INSERT INTO week_items VALUES (1, 1, '2026-11-04', 'Legacy plan', 1)")
        connection.execute("INSERT INTO week_reviews VALUES (1, '2026-11-04', 'Legacy review')")
    migrate("head")

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT title, status, coexecutor_ids, observer_ids, result, version FROM tasks"
        ).fetchone() == ("Legacy task", "in_progress", "[]", "[]", "", 1)
        assert connection.execute("SELECT title, done FROM week_items").fetchone() == (
            "Legacy plan",
            1,
        )
        assert connection.execute("SELECT text FROM week_reviews").fetchone() == ("Legacy review",)
        assert connection.execute(
            "SELECT user_id, week, closed_at FROM week_states"
        ).fetchall() == [(1, "2026-11-04", None)]
