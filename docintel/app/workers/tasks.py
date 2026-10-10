"""
Celery tasks — the actual background jobs. Kept thin: they just wire up a
sync DB session and delegate to the ingestion_service for real logic.
"""
import base64
import uuid

from app.core.database import SyncSessionLocal
from app.services.ingestion_service import process_document
from app.workers.celery_app import celery_app


@celery_app.task(name="ingest_document_from_file", bind=True, max_retries=2)
def ingest_document_from_file_task(self, document_id: str, file_bytes_b64: str):
    """file_bytes_b64: base64-encoded file content (Celery messages must be JSON-serializable)."""
    db = SyncSessionLocal()
    try:
        file_bytes = base64.b64decode(file_bytes_b64)
        process_document(db, uuid.UUID(document_id), file_bytes=file_bytes)
    finally:
        db.close()


@celery_app.task(name="ingest_document_from_url", bind=True, max_retries=2)
def ingest_document_from_url_task(self, document_id: str):
    db = SyncSessionLocal()
    try:
        process_document(db, uuid.UUID(document_id))
    finally:
        db.close()


@celery_app.task(name="ingest_document_from_text", bind=True)
def ingest_document_from_text_task(self, document_id: str, raw_text: str):
    db = SyncSessionLocal()
    try:
        process_document(db, uuid.UUID(document_id), raw_text=raw_text)
    finally:
        db.close()