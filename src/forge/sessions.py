"""Small SQLite-backed conversation store."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SessionStore:
    def __init__(self, database: Path) -> None:
        self.connection = sqlite3.connect(database)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS messages (session TEXT, role TEXT, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        self.connection.commit()

    def add(self, session: str, role: str, content: str) -> None:
        self.connection.execute(
            "INSERT INTO messages(session, role, content) VALUES (?, ?, ?)",
            (session, role, content),
        )
        self.connection.commit()

