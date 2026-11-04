"""SQLite persistence for local chat history."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "storage" / "database" / "conversations.sqlite3"


class ConversationStore:
    def __init__(self, path: Path = DEFAULT_DATABASE) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                );
                CREATE INDEX IF NOT EXISTS messages_conversation_idx
                    ON messages(conversation_id, id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def ensure_conversation(self, conversation_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO conversations (id) VALUES (?)", (conversation_id,)
            )

    def add_turn(self, conversation_id: str, user_text: str, assistant_text: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO conversations (id) VALUES (?)", (conversation_id,)
            )
            connection.executemany(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (
                    (conversation_id, "user", user_text),
                    (conversation_id, "assistant", assistant_text),
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') "
                "WHERE id = ?",
                (conversation_id,),
            )

    def recent_messages(self, conversation_id: str, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content FROM (
                    SELECT id, role, content FROM messages
                    WHERE conversation_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id
                """,
                (conversation_id, limit),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def list_conversations(self, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.updated_at,
                    (SELECT content FROM messages m WHERE m.conversation_id = c.id
                     ORDER BY m.id DESC LIMIT 1) AS preview
                FROM conversations c ORDER BY c.updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
