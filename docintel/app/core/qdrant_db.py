"""
Qdrant client singleton + collection bootstrap.

Design: ONE shared collection ("document_chunks") for all tenants, with
workspace_id stored as payload and used as a mandatory filter on every
query. This is simpler to operate than one-collection-per-tenant and scales
fine to thousands of tenants; if a single workspace ever gets huge, we can
shard later without changing the API surface.
"""
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType

from app.core.config import settings

COLLECTION_NAME = "document_chunks"


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection_exists() -> None:
    """Idempotent — safe to call on every startup."""
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=settings.EMBEDDING_DIM, distance=Distance.COSINE),
        )
        # Payload indexes make workspace/document filtering fast at scale.
        client.create_payload_index(COLLECTION_NAME, "workspace_id", PayloadSchemaType.KEYWORD)
        client.create_payload_index(COLLECTION_NAME, "document_id", PayloadSchemaType.KEYWORD)