"""Unit and integration tests for authentication and multi-user conversation isolation (IDOR)."""

import os
import pytest
from fastapi import HTTPException
from src.auth import get_current_user
from src.config import settings
from src.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    init_db,
    list_conversations,
)


@pytest.fixture(autouse=True)
def setup_test_sqlite(tmp_path, monkeypatch):
    """Use an isolated temporary SQLite database for each test."""
    db_file = tmp_path / "test_conversations.sqlite3"
    monkeypatch.setattr(settings, "SQLITE_PATH", str(db_file))
    init_db()


def test_auth_valid_demo_tokens():
    """Verify that Demo Token A and B map to their respective server-side user identities."""
    user_a = get_current_user(f"Bearer {settings.DEMO_TOKEN_A}")
    assert user_a.id == "user_a"

    user_b = get_current_user(f"Bearer {settings.DEMO_TOKEN_B}")
    assert user_b.id == "user_b"


def test_auth_invalid_and_missing_token():
    """Verify that invalid or missing tokens raise HTTP 401 Unauthorized."""
    # Missing header
    with pytest.raises(HTTPException) as exc1:
        get_current_user(None)
    assert exc1.value.status_code == 401

    # Bad format
    with pytest.raises(HTTPException) as exc2:
        get_current_user("Basic dXNlcjpwYXNz")
    assert exc2.value.status_code == 401

    # Invalid token string
    with pytest.raises(HTTPException) as exc3:
        get_current_user("Bearer fake-malicious-token")
    assert exc3.value.status_code == 401


def test_conversation_creation_and_listing_isolation():
    """Verify conversations created by User A are never visible to User B."""
    conv_a = create_conversation("user_a", title="Analisis Agustus")
    conv_b = create_conversation("user_b", title="Analisis September")

    list_a = list_conversations("user_a")
    list_b = list_conversations("user_b")

    # User A only sees conv_a
    ids_a = [c["id"] for c in list_a]
    assert conv_a["id"] in ids_a
    assert conv_b["id"] not in ids_a

    # User B only sees conv_b
    ids_b = [c["id"] for c in list_b]
    assert conv_b["id"] in ids_b
    assert conv_a["id"] not in ids_b


def test_idor_cross_user_read_blocked():
    """Verify that User B cannot read User A's conversation (returns None -> 404)."""
    conv_a = create_conversation("user_a", title="Data Rahasia User A")
    add_message("user_a", conv_a["id"], "user", "Pertanyaan rahasia A")

    # User A can read
    detail_a = get_conversation("user_a", conv_a["id"])
    assert detail_a is not None
    assert len(detail_a["messages"]) == 1

    # User B cannot read (returns None to signal 404)
    detail_b = get_conversation("user_b", conv_a["id"])
    assert detail_b is None


def test_idor_cross_user_write_blocked():
    """Verify that User B cannot append messages to User A's conversation."""
    conv_a = create_conversation("user_a", title="Percakapan Asli A")
    add_message("user_a", conv_a["id"], "user", "Pesan 1 dari A")

    # User B attempts to append message to User A's conversation
    result = add_message("user_b", conv_a["id"], "user", "Injeksi ilegal dari B")
    assert result is None  # Action rejected

    # Verify User A's conversation remains unchanged
    detail_a = get_conversation("user_a", conv_a["id"])
    assert len(detail_a["messages"]) == 1
    assert detail_a["messages"][0]["content"] == "Pesan 1 dari A"


def test_delete_conversation_success():
    """Verify that User A can delete their own conversation and cascade messages."""
    conv_a = create_conversation("user_a", title="Percakapan Untuk Dihapus")
    add_message("user_a", conv_a["id"], "user", "Pesan sebelum dihapus")

    # Delete conversation
    success = delete_conversation("user_a", conv_a["id"])
    assert success is True

    # Verification: conversation and messages no longer exist
    assert get_conversation("user_a", conv_a["id"]) is None
    ids_a = [c["id"] for c in list_conversations("user_a")]
    assert conv_a["id"] not in ids_a


def test_idor_cross_user_delete_blocked():
    """Verify that User B cannot delete User A's conversation."""
    conv_a = create_conversation("user_a", title="Percakapan Milik A")
    add_message("user_a", conv_a["id"], "user", "Pesan penting A")

    # User B attempts to delete User A's conversation
    success = delete_conversation("user_b", conv_a["id"])
    assert success is False

    # Verify User A's conversation is still intact
    detail_a = get_conversation("user_a", conv_a["id"])
    assert detail_a is not None
    assert len(detail_a["messages"]) == 1

