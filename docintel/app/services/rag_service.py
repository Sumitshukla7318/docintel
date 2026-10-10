"""
Core RAG orchestration: takes a user question, (optionally) condenses it
using conversation history, retrieves relevant chunks from Qdrant, builds a
grounded prompt, calls the LLM, and maps citations back to source documents.

This is the "agent" layer — right now it's a single-hop retrieve-then-answer
agent. It's structured so a future multi-step/tool-using agent loop can slot
in without touching the API layer.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.services.embedding_service import embed_query
from app.services.llm_service import condense_query, generate_answer
from app.services.vector_store_service import search_similar_chunks
from app.utils.prompt import RAG_SYSTEM_PROMPT, build_rag_user_prompt


async def _get_document_titles(db: AsyncSession, document_ids: list[str]) -> dict[str, str]:
    if not document_ids:
        return {}
    uuids = [uuid.UUID(d) for d in document_ids]
    result = await db.execute(select(Document.id, Document.title).where(Document.id.in_(uuids)))
    return {str(row.id): row.title for row in result.all()}


async def answer_question(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    question: str,
    conversation_history: str = "",
    document_ids: list[uuid.UUID] | None = None,
    top_k: int | None = None,
) -> tuple[str, list[dict]]:
    """
    Returns (answer_text, citations) where citations is a list of dicts
    matching the Citation schema shape.
    """
    top_k = top_k or settings.DEFAULT_TOP_K

    # Step 1: condense the question using history, if there's a conversation going.
    effective_question = question
    if conversation_history.strip():
        try:
            effective_question = condense_query(conversation_history, question)
        except Exception:
            # If condensing fails for any reason (e.g. rate limit), fall back to the raw question
            # rather than failing the whole request.
            effective_question = question

    # Step 2: embed + retrieve
    query_vector = embed_query(effective_question)
    doc_id_strs = [str(d) for d in document_ids] if document_ids else None
    retrieved_chunks = search_similar_chunks(
        workspace_id=workspace_id,
        query_vector=query_vector,
        top_k=top_k,
        document_ids=document_ids,
    )

    if not retrieved_chunks:
        return (
            "I couldn't find any relevant information in your documents to answer this question. "
            "Try rephrasing, or upload a document that covers this topic.",
            [],
        )

    # Step 3: resolve document titles for citation display
    unique_doc_ids = list({c["document_id"] for c in retrieved_chunks})
    titles = await _get_document_titles(db, unique_doc_ids)
    for chunk in retrieved_chunks:
        chunk["document_title"] = titles.get(chunk["document_id"], "Unknown document")

    # Step 4: build grounded prompt + generate
    user_prompt = build_rag_user_prompt(effective_question, retrieved_chunks, conversation_history)
    answer = generate_answer(RAG_SYSTEM_PROMPT, user_prompt)

    # Step 5: build citation payloads
    citations = [
        {
            "document_id": chunk["document_id"],
            "document_title": chunk["document_title"],
            "chunk_id": str(chunk["chunk_id"]),
            "chunk_index": chunk["chunk_index"],
            "snippet": chunk["content"][:300],
            "score": round(float(chunk["score"]), 4),
        }
        for chunk in retrieved_chunks
    ]

    return answer, citations