"""
Orchestrates the full ingestion pipeline for one document:
parse -> chunk -> embed -> store (Qdrant + Postgres chunk metadata).

This function is intentionally synchronous (uses the sync DB session) because
it's designed to be called from a Celery task, not from an async FastAPI route.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.chunking_service import chunk_text, count_tokens
from app.services.document_parser import ParsingError, parse_file, parse_url
from app.services.embedding_service import embed_texts
from app.services.vector_store_service import upsert_chunks


class IngestionError(Exception):
    pass


def process_document(db: Session, document_id: uuid.UUID, raw_text: str | None = None, file_bytes: bytes | None = None) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise IngestionError(f"Document {document_id} not found")

    try:
        document.status = DocumentStatus.PROCESSING
        db.commit()

        # 1. Get raw text depending on source type
        if raw_text is not None:
            text = raw_text
        elif document.source_type.value == "url":
            text = parse_url(document.source_uri)
        elif file_bytes is not None:
            text = parse_file(document.source_type, file_bytes)
        else:
            raise IngestionError("No content available to process")

        # 2. Chunk
        chunks = chunk_text(text)
        if not chunks:
            raise IngestionError("Document produced zero chunks after parsing")

        # 3. Embed (batched, single call to the local model for efficiency)
        vectors = embed_texts(chunks)

        # 4. Persist chunk metadata rows in Postgres
        chunk_records = []
        for idx, (chunk_content, vector) in enumerate(zip(chunks, vectors)):
            chunk_row = DocumentChunk(
                document_id=document.id,
                workspace_id=document.workspace_id,
                chunk_index=idx,
                content=chunk_content,
                token_count=count_tokens(chunk_content),
            )
            db.add(chunk_row)
            db.flush()  # get chunk_row.id
            chunk_records.append({
                "chunk_id": chunk_row.id,
                "vector": vector,
                "content": chunk_content,
                "chunk_index": idx,
            })

        # 5. Store vectors in Qdrant
        upsert_chunks(document.workspace_id, document.id, chunk_records)

        # 6. Mark complete
        document.status = DocumentStatus.COMPLETED
        document.num_chunks = len(chunks)
        document.error_message = None
        db.commit()

    except (ParsingError, IngestionError) as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        db.commit()
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = f"Unexpected error: {exc}"
        db.commit()
        raise