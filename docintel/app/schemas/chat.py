import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.chat import MessageRole


class Citation(BaseModel):
    document_id: uuid.UUID
    document_title: str
    chunk_id: str
    chunk_index: int
    snippet: str
    score: float


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str
    citations: list[Citation] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetailOut(ChatSessionOut):
    messages: list[ChatMessageOut]


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID | None = Field(default=None, description="Omit to start a new session")
    document_ids: list[uuid.UUID] | None = Field(default=None, description="Optionally restrict retrieval to specific documents")
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatQueryResponse(BaseModel):
    session_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: list[Citation]
    used_cache: bool = False