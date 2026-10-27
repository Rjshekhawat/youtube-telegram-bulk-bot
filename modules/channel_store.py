"""SQLite-backed channel configuration."""
import sqlite3
from pathlib import Path

DB_PATH = Path("bot_manager.sqlite3")
VALID_MODULES = {"news", "question", "pdf"}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            label TEXT NOT NULL,
            UNIQUE(module, chat_id)
        )"""
    )
    return conn


def add_channel(module: str, chat_id: str, label: str | None = None) -> bool:
    module = module.lower().strip()
    if module not in VALID_MODULES:
        raise ValueError("Module must be news, question, or pdf.")
    chat_id = chat_id.strip()
    if not chat_id:
        raise ValueError("Channel ID or @username is required.")
    with _connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO channels(module, chat_id, label) VALUES (?, ?, ?)",
            (module, chat_id, (label or chat_id).strip()),
        )
        return cur.rowcount > 0


def remove_channel(channel_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        return cur.rowcount > 0


def list_channels():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, module, chat_id, label FROM channels ORDER BY module, id"
        ).fetchall()
    return rows


def get_channels(module: str):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT chat_id FROM channels WHERE module = ? ORDER BY id",
            (module.lower().strip(),),
        ).fetchall()
    return [row[0] for row in rows]
