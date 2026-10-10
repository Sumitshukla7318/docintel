"""
Import all models here so that Base.metadata is fully populated
for Alembic autogenerate and for create_all in dev/testing.
"""
from app.models.user import User, Workspace, UserRole  # noqa: F401
from app.models.document import Document, DocumentChunk, DocumentSourceType, DocumentStatus  # noqa: F401
from app.models.chat import ChatSession, ChatMessage, MessageRole  # noqa: F401