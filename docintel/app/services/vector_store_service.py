"""
Thin wrapper around Qdrant operations — upsert, search, delete — all scoped
by workspace_id so tenants can never see each other's vectors even if a bug
elsewhere forgets to filter (defense in depth).
"""
import uuid

from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
)

from app.core.qdrant_db import COLLECTION_NAME, get_qdrant_client


def upsert_chunks(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    chunk_records: list[dict],
) -> None:
    """
    chunk_records: [{"chunk_id": uuid, "vector": [...], "content": str, "chunk_index": int}, ...]
    """
    client = get_qdrant_client()
    points = [
        PointStruct(
            id=str(record["chunk_id"]),
            vector=record["vector"],
            payload={
                "workspace_id": str(workspace_id),
                "document_id": str(document_id),
                "chunk_index": record["chunk_index"],
                "content": record["content"],
            },
        )
        for record in chunk_records
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search_similar_chunks(
    workspace_id: uuid.UUID,
    query_vector: list[float],
    top_k: int = 5,
    document_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Vector similarity search, always filtered to the caller's workspace.
    Optionally further scoped to a subset of document_ids (e.g. user picked
    specific sources to query against). Uses MatchAny for the multi-id case
    so filtering by more than one document actually works correctly.
    """
    client = get_qdrant_client()

    must_conditions = [
        FieldCondition(key="workspace_id", match=MatchValue(value=str(workspace_id)))
    ]

    if document_ids:
        id_strs = [str(d) for d in document_ids]
        if len(id_strs) == 1:
            must_conditions.append(FieldCondition(key="document_id", match=MatchValue(value=id_strs[0])))
        else:
            must_conditions.append(FieldCondition(key="document_id", match=MatchAny(any=id_strs)))

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(must=must_conditions),
        limit=top_k,
    )

    return [
        {
            "chunk_id": point.id,
            "score": point.score,
            "document_id": point.payload.get("document_id"),
            "chunk_index": point.payload.get("chunk_index"),
            "content": point.payload.get("content"),
        }
        for point in results
    ]


def delete_document_vectors(document_id: uuid.UUID) -> None:
    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
        ),
    )