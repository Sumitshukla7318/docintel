"""
Async Redis client singleton — used for response caching and (later) rate
limiting. Kept separate from Celery's Redis usage (different DB index) so
cache flushes never touch the task queue.
"""
import json
from functools import lru_cache
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

CACHE_TTL_SECONDS = 60 * 30  # 30 minutes — long enough to help repeat queries, short enough to not go stale


@lru_cache
def get_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def cache_get(key: str) -> Any | None:
    client = get_redis_client()
    raw = await client.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    client = get_redis_client()
    await client.set(key, json.dumps(value), ex=ttl)


def build_query_cache_key(workspace_id: str, query: str, document_ids: list[str] | None) -> str:
    doc_part = ",".join(sorted(document_ids)) if document_ids else "all"
    return f"rag_query:{workspace_id}:{doc_part}:{query.strip().lower()}"