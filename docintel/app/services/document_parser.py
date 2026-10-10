"""
Parses raw source bytes/URLs into plain text, regardless of source format.
Each function returns plain extracted text — chunking happens downstream.
"""
import io

import pandas as pd
import requests
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.models.document import DocumentSourceType


class ParsingError(Exception):
    pass


def parse_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        raise ParsingError("No extractable text found in PDF (it may be a scanned/image-only PDF)")
    return text


def parse_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ParsingError("No extractable text found in DOCX")
    return text


def parse_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore").strip()


def parse_csv(file_bytes: bytes) -> str:
    df = pd.read_csv(io.BytesIO(file_bytes))
    return df.to_string(index=False)


def parse_xlsx(file_bytes: bytes) -> str:
    df = pd.read_excel(io.BytesIO(file_bytes))
    return df.to_string(index=False)


def parse_url(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "DocIntel/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ParsingError(f"Failed to fetch URL: {exc}") from exc

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    if not text:
        raise ParsingError("No extractable text found on the page")
    return text


PARSER_MAP = {
    DocumentSourceType.FILE_PDF: parse_pdf,
    DocumentSourceType.FILE_DOCX: parse_docx,
    DocumentSourceType.FILE_TXT: parse_txt,
    DocumentSourceType.FILE_CSV: parse_csv,
    DocumentSourceType.FILE_XLSX: parse_xlsx,
}


def parse_file(source_type: DocumentSourceType, file_bytes: bytes) -> str:
    parser = PARSER_MAP.get(source_type)
    if parser is None:
        raise ParsingError(f"No parser available for source type: {source_type}")
    return parser(file_bytes)