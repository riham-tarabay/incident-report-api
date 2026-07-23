"""Migration tests: verify the Alembic upgrade/downgrade path actually runs."""
import os
import pathlib
import sqlite3
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _run_alembic(args, env):
    # Use sys.executable -m alembic (not the bare "alembic" command) so the
    # tests work on any OS regardless of how the venv exposes console scripts.
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _columns(db_path):
    con = sqlite3.connect(db_path)
    try:
        return [row[1] for row in con.execute("PRAGMA table_info(incidents)")]
    finally:
        con.close()


def test_upgrade_head_creates_full_schema(tmp_path):
    db_path = tmp_path / "migrate.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}

    _run_alembic(["upgrade", "head"], env)

    cols = _columns(db_path)
    for expected in ["id", "title", "description", "severity", "status", "reporter_email", "created_at", "updated_at", "resolution_notes"]:
        assert expected in cols


def test_downgrade_removes_resolution_notes(tmp_path):
    db_path = tmp_path / "migrate.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}

    _run_alembic(["upgrade", "head"], env)
    assert "resolution_notes" in _columns(db_path)

    _run_alembic(["downgrade", "-1"], env)
    assert "resolution_notes" not in _columns(db_path)

    # And the path back up works too.
    _run_alembic(["upgrade", "head"], env)
    assert "resolution_notes" in _columns(db_path)
