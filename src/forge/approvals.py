"""Persistent approval records for actions that can change a project."""

from __future__ import annotations

import sqlite3
import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class Approval:
    id: str
    action: str
    summary: str
    payload: dict[str, object]
    status: str


class ApprovalStore:
    def __init__(self, database: Path | str) -> None:
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.lock = Lock()
        with self.lock:
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, action TEXT, summary TEXT, payload TEXT NOT NULL DEFAULT '{}', status TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            columns = {row[1] for row in self.connection.execute("PRAGMA table_info(approvals)")}
            if "payload" not in columns:
                self.connection.execute("ALTER TABLE approvals ADD COLUMN payload TEXT NOT NULL DEFAULT '{}'")
            self.connection.commit()

    def request(self, action: str, summary: str, payload: dict[str, object] | None = None) -> Approval:
        approval = Approval(uuid4().hex[:8], action, summary, payload or {}, "pending")
        with self.lock:
            self.connection.execute(
                "INSERT INTO approvals(id, action, summary, payload, status) VALUES (?, ?, ?, ?, ?)",
                (approval.id, approval.action, approval.summary, json.dumps(approval.payload), approval.status),
            )
            self.connection.commit()
        return approval

    def list(self, status: str = "pending") -> list[Approval]:
        with self.lock:
            rows = self.connection.execute(
                "SELECT id, action, summary, payload, status FROM approvals WHERE status = ? ORDER BY created_at DESC, rowid DESC",
                (status,),
            ).fetchall()
        return [Approval(row[0], row[1], row[2], json.loads(row[3]), row[4]) for row in rows]

    def decide(self, approval_id: str, approve: bool) -> Approval | None:
        status = "approved" if approve else "rejected"
        with self.lock:
            cursor = self.connection.execute(
                "UPDATE approvals SET status = ? WHERE id = ? AND status = 'pending'",
                (status, approval_id),
            )
            self.connection.commit()
            if cursor.rowcount != 1:
                return None
            row = self.connection.execute(
                "SELECT id, action, summary, payload, status FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        return Approval(row[0], row[1], row[2], json.loads(row[3]), row[4])
