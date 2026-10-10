import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.models.document import DocumentSourceType, DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    source_type: DocumentSourceType
    source_uri: str | None
    status: DocumentStatus
    file_size_bytes: int | None
    num_chunks: int | None
    error_message: str | None
    task_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentIngestUrl(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, description="Optional display title; defaults to the URL")


class DocumentIngestText(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)


class ChunkPreview(BaseModel):
    chunk_index: int
    content: str
    token_count: int | None