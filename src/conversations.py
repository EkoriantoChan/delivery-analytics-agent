"""SQLite storage for conversations and messages with strict ownership isolation."""

from __future__ import annotations

import datetime
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import settings


def get_db_path() -> Path:
    """Return the resolved Path to SQLite database, ensuring parent directory exists."""
    path = Path(settings.SQLITE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initialize SQLite tables for conversations and messages."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations (user_id, updated_at DESC);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                data_basis TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages (conversation_id, created_at ASC);
            """
        )


def _current_timestamp() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def create_conversation(user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Create a new conversation strictly owned by user_id."""
    init_db()
    conv_id = str(uuid.uuid4())
    now = _current_timestamp()
    conv_title = title.strip() if title and title.strip() else "Percakapan Baru"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conv_id, user_id, conv_title, now, now),
        )

    return {
        "id": conv_id,
        "title": conv_title,
        "created_at": now,
        "updated_at": now,
    }


def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    """List all conversations owned by user_id, ordered by updated_at descending."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, title, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


def get_conversation(user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation and messages if and only if owned by user_id.

    Returns None if conversation does not exist OR is owned by another user.
    """
    init_db()
    with get_connection() as conn:
        # Check ownership
        cursor = conn.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )
        conv = cursor.fetchone()
        if not conv:
            return None

        # Fetch messages in chronological order
        msg_cursor = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )
        messages = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "created_at": msg["created_at"],
            }
            for msg in msg_cursor.fetchall()
        ]

        return {
            "id": conv["id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "messages": messages,
        }


def add_message(
    user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    data_basis: str = "",
    outcome: str = "",
) -> Optional[Dict[str, Any]]:
    """Add a message to a conversation owned by user_id.

    Returns None if conversation does not belong to user_id (prevents IDOR).
    """
    init_db()
    now = _current_timestamp()
    msg_id = str(uuid.uuid4())

    with get_connection() as conn:
        # Verify ownership
        cursor = conn.execute(
            "SELECT id, title FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        conv = cursor.fetchone()
        if not conv:
            return None

        # Insert message
        conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at, data_basis, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (msg_id, conversation_id, role, content, now, data_basis, outcome),
        )

        # Update conversation title if first user message and default title
        new_title = conv["title"]
        if role == "user" and conv["title"] == "Percakapan Baru":
            snippet = content.strip().replace("\n", " ")
            new_title = snippet[:40] + ("..." if len(snippet) > 40 else "")

        conn.execute(
            """
            UPDATE conversations
            SET updated_at = ?, title = ?
            WHERE id = ? AND user_id = ?
            """,
            (now, new_title, conversation_id, user_id),
        )

    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "created_at": now,
        "data_basis": data_basis,
        "outcome": outcome,
    }


def get_recent_history(user_id: str, conversation_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """Retrieve the recent message history for agent context."""
    conv = get_conversation(user_id, conversation_id)
    if not conv:
        return []
    messages = conv.get("messages", [])
    return messages[-limit:]


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    """Delete a conversation and all its messages if and only if owned by user_id.

    Returns True if deleted, False if conversation does not exist or belongs to another user.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        return cursor.rowcount > 0

