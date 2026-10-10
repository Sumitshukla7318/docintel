"""
Document model — represents one ingested source (file upload, URL, raw text).
Actual vector chunks live in Qdrant, not Postgres; this table is the
source-of-truth metadata + processing status tracker for the Celery pipeline.
"""
import enum
import uuid

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class DocumentSourceType(str, enum.Enum):
    FILE_PDF = "file_pdf"
    FILE_DOCX = "file_docx"
    FILE_TXT = "file_txt"
    FILE_CSV = "file_csv"
    FILE_XLSX = "file_xlsx"
    URL = "url"
    RAW_TEXT = "raw_text"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"        # uploaded, queued for processing
    PROCESSING = "processing"  # celery worker actively parsing/chunking/embedding
    COMPLETED = "completed"    # indexed in Qdrant, ready for retrieval
    FAILED = "failed"


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[DocumentSourceType] = mapped_column(SAEnum(DocumentSourceType))
    source_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)   # file path or URL
    status: Mapped[DocumentStatus] = mapped_column(SAEnum(DocumentStatus), default=DocumentStatus.PENDING)

    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    num_chunks: Mapped[int | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Celery task id for status polling
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """
    Lightweight Postgres mirror of each chunk's metadata (NOT the vector itself —
    the embedding lives in Qdrant, keyed by this row's id). Keeping a Postgres
    record lets us do fast lookups, joins, and full-text fallback search
    without round-tripping to Qdrant for metadata.
    """
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)

    chunk_index: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")