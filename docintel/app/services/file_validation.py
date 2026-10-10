"""
Validates that uploaded file *content* actually matches its claimed type —
extension alone is trivially spoofable (rename malware.exe to notes.txt).
"""
import magic

from app.models.document import DocumentSourceType

# Maps our source types to the set of real MIME types libmagic may report
# for a genuine file of that kind. PDFs and Office formats have very
# distinctive magic bytes; plain text is inherently permissive since any
# byte sequence can technically be "text".
ALLOWED_MIME_TYPES: dict[DocumentSourceType, set[str]] = {
    DocumentSourceType.FILE_PDF: {"application/pdf"},
    DocumentSourceType.FILE_DOCX: {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",  # docx is a zip container; some libmagic versions report this
    },
    DocumentSourceType.FILE_XLSX: {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    },
    DocumentSourceType.FILE_TXT: {"text/plain", "text/x-python", "application/csv"},
    DocumentSourceType.FILE_CSV: {"text/plain", "text/csv", "application/csv"},
}


class FileValidationError(Exception):
    pass


def validate_file_content(file_bytes: bytes, expected_type: DocumentSourceType, filename: str) -> None:
    """Raises FileValidationError if the file's actual content doesn't match its claimed type."""
    if not file_bytes:
        raise FileValidationError("Uploaded file is empty")

    detected_mime = magic.from_buffer(file_bytes[:2048], mime=True)
    allowed = ALLOWED_MIME_TYPES.get(expected_type)

    if allowed and detected_mime not in allowed:
        raise FileValidationError(
            f"File '{filename}' doesn't look like a valid {expected_type.value.replace('file_', '').upper()} "
            f"file (detected: {detected_mime}). It may be corrupted or mislabeled."
        )