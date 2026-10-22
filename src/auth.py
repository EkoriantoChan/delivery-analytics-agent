"""Authentication module for bearer token verification and identity mapping."""

from __future__ import annotations

from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from src.config import settings


class User(BaseModel):
    """Authenticated user identity resolved server-side from bearer token."""
    id: str
    token: str


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """FastAPI dependency to extract and verify the demo bearer token.

    Identity is strictly derived on the server side from the verified token.
    Client-provided user_id is ignored to prevent authorization bypass.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization diperlukan",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format Bearer token tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Map demo tokens to server-side user identities
    if token == settings.DEMO_TOKEN_A:
        return User(id="user_a", token=token)
    elif token == settings.DEMO_TOKEN_B:
        return User(id="user_b", token=token)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token tidak valid atau tidak dikenal",
            headers={"WWW-Authenticate": "Bearer"},
        )
