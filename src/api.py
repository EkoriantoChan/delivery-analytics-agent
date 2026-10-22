"""FastAPI REST API implementing the full participant delivery analytics contract."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent import run_agent_workflow
from src.auth import User, get_current_user
from src.config import settings
from src.conversations import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_recent_history,
    init_db,
    list_conversations,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Delivery Analytics Agent API",
    description="Backend API for delivery operations analytics agent querying Neon Gold schema.",
    version="1.0.0",
)

# Enable CORS for local testing and UI clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables on application startup."""
    init_db()


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: str


class ListConversationsResponse(BaseModel):
    conversations: List[ConversationSummary]


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ConversationDetailResponse(BaseModel):
    id: str
    messages: List[ChatMessage]


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=settings.MAX_PROMPT_LENGTH)


class SendMessageResponse(BaseModel):
    conversation_id: str
    answer: str
    data_basis: str
    outcome: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/healthz", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Public healthcheck endpoint for Docker Compose and monitoring."""
    return {"status": "ok"}


@app.get(
    "/api/v1/conversations",
    response_model=ListConversationsResponse,
    tags=["Conversations"],
)
def get_user_conversations(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """List all conversations strictly owned by the authenticated bearer token user."""
    items = list_conversations(current_user.id)
    return {"conversations": items}


@app.post(
    "/api/v1/conversations",
    status_code=status.HTTP_201_CREATED,
    response_model=ConversationSummary,
    tags=["Conversations"],
)
def create_new_conversation(
    req: CreateConversationRequest = CreateConversationRequest(),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new conversation assigned strictly to the authenticated user."""
    created = create_conversation(current_user.id, title=req.title)
    return created


@app.get(
    "/api/v1/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    tags=["Conversations"],
)
def read_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Fetch conversation and messages.

    Returns 404 if the conversation does not exist OR belongs to another user (IDOR prevention).
    """
    conv = get_conversation(current_user.id, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Percakapan tidak ditemukan",
        )
    return conv


@app.delete(
    "/api/v1/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    tags=["Conversations"],
)
def remove_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a conversation and its messages if and only if owned by current user.

    Returns 404 if the conversation does not exist OR belongs to another user (IDOR prevention).
    """
    deleted = delete_conversation(current_user.id, conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Percakapan tidak ditemukan",
        )
    return {"status": "deleted", "id": conversation_id}



@app.post(
    "/api/v1/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    tags=["Messages"],
)
def send_conversation_message(
    conversation_id: str,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Send user message, invoke agent with conversation history context, and persist response.

    Returns 404 if the conversation does not exist OR belongs to another user (IDOR prevention).
    """
    user_prompt = req.content.strip()

    # Step 1: Verify conversation exists and belongs to current user
    existing = get_conversation(current_user.id, conversation_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Percakapan tidak ditemukan",
        )

    # Step 2: Retrieve recent history for context resolution before adding this message
    recent_history = get_recent_history(
        current_user.id,
        conversation_id,
        limit=settings.MAX_MESSAGE_HISTORY,
    )

    # Step 3: Record user message
    user_msg = add_message(
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="user",
        content=user_prompt,
    )
    if not user_msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Percakapan tidak ditemukan",
        )

    # Step 4: Run Agent Workflow
    agent_output = run_agent_workflow(
        user_prompt=user_prompt,
        history=recent_history,
    )

    # Step 5: Record assistant message
    add_message(
        user_id=current_user.id,
        conversation_id=conversation_id,
        role="assistant",
        content=agent_output.answer,
        data_basis=agent_output.data_basis,
        outcome=agent_output.outcome,
    )

    return {
        "conversation_id": conversation_id,
        "answer": agent_output.answer,
        "data_basis": agent_output.data_basis,
        "outcome": agent_output.outcome,
    }
