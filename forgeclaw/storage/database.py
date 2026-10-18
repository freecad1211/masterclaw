import json
import sqlite3
from pathlib import Path
from typing import Any


def _connect(database_path: str) -> sqlite3.Connection:
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def check_database(database_path: str) -> None:
    with _connect(database_path) as connection:
        connection.execute("SELECT 1").fetchone()


def initialize_database(database_path: str) -> None:
    with _connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("""CREATE TABLE IF NOT EXISTS debates (
            id TEXT PRIMARY KEY, topic TEXT NOT NULL, status TEXT NOT NULL,
            decision TEXT NOT NULL, created_at TEXT NOT NULL, payload_json TEXT NOT NULL)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS developer_runs (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, payload_json TEXT NOT NULL)""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_developer_runs_updated ON developer_runs(updated_at DESC)")


def save_developer_run(database_path: str, record: dict[str, Any]) -> None:
    with _connect(database_path) as connection:
        connection.execute("""INSERT INTO developer_runs (id, status, created_at, updated_at, payload_json)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,
            updated_at=excluded.updated_at, payload_json=excluded.payload_json""",
            (record["id"], record["status"], record["created_at"], record["updated_at"],
             json.dumps(record, ensure_ascii=False)))


def get_developer_run(database_path: str, run_id: str) -> dict[str, Any] | None:
    with _connect(database_path) as connection:
        row = connection.execute("SELECT payload_json FROM developer_runs WHERE id = ?", (run_id,)).fetchone()
    return json.loads(row["payload_json"]) if row else None


def list_developer_runs(database_path: str, limit: int = 50) -> list[dict[str, Any]]:
    with _connect(database_path) as connection:
        rows = connection.execute("SELECT payload_json FROM developer_runs ORDER BY updated_at DESC LIMIT ?",
                                  (max(1, min(limit, 200)),)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def save_debate(database_path: str, record: dict[str, Any]) -> None:
    with _connect(database_path) as connection:
        connection.execute("""INSERT INTO debates (id, topic, status, decision, created_at, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (record["id"], record["topic"], record["status"], record["decision"],
             record["created_at"], json.dumps(record, ensure_ascii=False)))


def get_debate(database_path: str, debate_id: str) -> dict[str, Any] | None:
    with _connect(database_path) as connection:
        row = connection.execute("SELECT payload_json FROM debates WHERE id = ?", (debate_id,)).fetchone()
    return json.loads(row["payload_json"]) if row else None


def list_debates(database_path: str, limit: int = 20) -> list[dict[str, Any]]:
    with _connect(database_path) as connection:
        rows = connection.execute("SELECT id, topic, status, decision, created_at FROM debates ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]
