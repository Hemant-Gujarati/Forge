"""Small SQLite-backed conversation store."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock


class SessionStore:
    def __init__(self, database: Path | str) -> None:
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.lock = Lock()
        with self.lock:
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS messages (session TEXT, role TEXT, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            self.connection.commit()

    def add(self, session: str, role: str, content: str) -> None:
        with self.lock:
            self.connection.execute(
                "INSERT INTO messages(session, role, content) VALUES (?, ?, ?)",
                (session, role, content),
            )
            self.connection.commit()

    def history(self, session: str, limit: int = 20) -> list[dict[str, str]]:
        with self.lock:
            rows = self.connection.execute(
                "SELECT role, content FROM messages WHERE session = ? ORDER BY created_at DESC, rowid DESC LIMIT ?",
                (session, limit),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

