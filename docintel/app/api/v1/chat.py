"""
Chat/query endpoints — the main "ask a question" surface of the product.
Includes response caching (identical question + same doc scope + same
workspace → served from Redis) to save LLM calls on repeat queries.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_workspace_id
from app.core.database import get_db
from app.core.redis_client import build_query_cache_key, cache_get, cache_set
from app.models.chat import MessageRole
from app.models.user import User
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionDetailOut,
    ChatSessionOut,
)
from app.services.chat_service import (
    add_message,
    create_session,
    get_recent_history_text,
    get_session,
    get_session_with_messages,
    list_sessions,
)

from app.services.rag_service import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_session(db, workspace_id, current_user.id)


@router.get("/sessions", response_model=list[ChatSessionOut])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_sessions(db, workspace_id, current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut)
async def get_chat_session_detail(
    session_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session_with_messages(db, session_id, workspace_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return ChatSessionDetailOut(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=session.messages,
    )


@router.post("/query", response_model=ChatQueryResponse)
async def query(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    # Resolve or create the session
    if payload.session_id:
        session = await get_session(db, payload.session_id, workspace_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    else:
        title = payload.message[:50] + ("..." if len(payload.message) > 50 else "")
        session = await create_session(db, workspace_id, current_user.id, title=title)

    # Persist the user's message immediately
    await add_message(db, session.id, MessageRole.USER, payload.message)

    # Check cache (only for fresh, single-turn-style questions — history makes answers context-dependent)
    doc_id_strs = [str(d) for d in payload.document_ids] if payload.document_ids else None
    cache_key = build_query_cache_key(str(workspace_id), payload.message, doc_id_strs)
    cached = await cache_get(cache_key)

    if cached:
        answer, citations = cached["answer"], cached["citations"]
        used_cache = True
    else:
        history_text = await get_recent_history_text(db, session.id, max_messages=6)
        answer, citations = await answer_question(
            db=db,
            workspace_id=workspace_id,
            question=payload.message,
            conversation_history=history_text,
            document_ids=payload.document_ids,
            top_k=payload.top_k,
        )
        await cache_set(cache_key, {"answer": answer, "citations": citations})
        used_cache = False

    assistant_message = await add_message(db, session.id, MessageRole.ASSISTANT, answer, citations=citations)

    return ChatQueryResponse(
        session_id=session.id,
        message_id=assistant_message.id,
        answer=answer,
        citations=citations,
        used_cache=used_cache,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id, workspace_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    await db.delete(session)
    await db.commit()