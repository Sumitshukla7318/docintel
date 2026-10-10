"""
Persistence layer for chat sessions/messages — kept separate from the RAG
orchestration so history management is independently testable.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession, MessageRole


async def create_session(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID, title: str = "New Chat") -> ChatSession:
    session = ChatSession(workspace_id=workspace_id, user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID, workspace_id: uuid.UUID) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


async def get_session_with_messages(db: AsyncSession, session_id: uuid.UUID, workspace_id: uuid.UUID) -> ChatSession | None:
    """
    Same as get_session, but eagerly loads the messages relationship via
    selectinload — required because accessing a lazy relationship after the
    fact isn't safe under async SQLAlchemy (it tries a sync-style lazy load
    outside the greenlet context and raises MissingGreenlet).
    """
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id, ChatSession.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.workspace_id == workspace_id, ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: MessageRole,
    content: str,
    citations: list[dict] | None = None,
) -> ChatMessage:
    message = ChatMessage(session_id=session_id, role=role, content=content, citations=citations)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_recent_history_text(db: AsyncSession, session_id: uuid.UUID, max_messages: int = 6) -> str:
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(max_messages)
    )
    messages = list(reversed(result.scalars().all()))
    lines = [f"{m.role.value.upper()}: {m.content}" for m in messages]
    return "\n".join(lines)