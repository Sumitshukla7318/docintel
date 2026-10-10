"""
Free, local embedding generation using sentence-transformers.
Model is loaded once (singleton) and reused across requests/workers to avoid
reloading weights on every call — this is the #1 perf killer if done wrong.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    """Cached singleton — model loads once per process (API worker or Celery worker)."""
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of texts. Returns one vector per input string, in order."""
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,  # cosine similarity works cleanly on normalized vectors
    )
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single query string (e.g. a user's question) for retrieval."""
    return embed_texts([text])[0]