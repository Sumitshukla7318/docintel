"""
Document management endpoints: upload files, ingest URLs/raw text, check
processing status, list, and delete. Every query is scoped to the caller's
workspace via get_workspace_id — no client-supplied workspace_id is ever
trusted.
"""
import base64
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_workspace_id
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document, DocumentSourceType, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentIngestText, DocumentIngestUrl, DocumentOut
from app.services.vector_store_service import delete_document_vectors
from app.workers.tasks import (
    ingest_document_from_file_task,
    ingest_document_from_text_task,
    ingest_document_from_url_task,
)

from app.services.file_validation import FileValidationError, validate_file_content

router = APIRouter(prefix="/documents", tags=["Documents"])

EXTENSION_MAP = {
    "pdf": DocumentSourceType.FILE_PDF,
    "docx": DocumentSourceType.FILE_DOCX,
    "txt": DocumentSourceType.FILE_TXT,
    "csv": DocumentSourceType.FILE_CSV,
    "xlsx": DocumentSourceType.FILE_XLSX,
}


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    source_type = EXTENSION_MAP.get(ext)
    if source_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Supported: {list(EXTENSION_MAP.keys())}",
        )

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds max size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    try:
        validate_file_content(file_bytes, source_type, file.filename)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    document = Document(
        workspace_id=workspace_id,
        uploaded_by_id=current_user.id,
        title=file.filename,
        source_type=source_type,
        status=DocumentStatus.PENDING,
        file_size_bytes=len(file_bytes),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    task = ingest_document_from_file_task.delay(
        str(document.id), base64.b64encode(file_bytes).decode("utf-8")
    )
    document.task_id = task.id
    await db.commit()
    await db.refresh(document)

    return document

@router.post("/ingest-url", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    payload: DocumentIngestUrl,
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    document = Document(
        workspace_id=workspace_id,
        uploaded_by_id=current_user.id,
        title=payload.title or str(payload.url),
        source_type=DocumentSourceType.URL,
        source_uri=str(payload.url),
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    task = ingest_document_from_url_task.delay(str(document.id))
    document.task_id = task.id
    await db.commit()
    await db.refresh(document)

    return document


@router.post("/ingest-text", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def ingest_text(
    payload: DocumentIngestText,
    current_user: User = Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    document = Document(
        workspace_id=workspace_id,
        uploaded_by_id=current_user.id,
        title=payload.title,
        source_type=DocumentSourceType.RAW_TEXT,
        status=DocumentStatus.PENDING,
        file_size_bytes=len(payload.content.encode("utf-8")),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    task = ingest_document_from_text_task.delay(str(document.id), payload.content)
    document.task_id = task.id
    await db.commit()
    await db.refresh(document)

    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.workspace_id == workspace_id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    delete_document_vectors(document.id)  # clean up Qdrant first
    await db.delete(document)             # cascades to document_chunks rows
    await db.commit()