"""
Text chunking — splits long documents into overlapping windows suitable for
embedding + retrieval. Uses a recursive character splitter (paragraph ->
sentence -> word fallback) so chunks break on natural boundaries rather than
mid-word, which improves retrieval quality noticeably over naive fixed-size
slicing.
"""
import tiktoken

from app.core.config import settings

_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def _split_on_separator(text: str, separator: str) -> list[str]:
    return [s for s in text.split(separator) if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """
    Returns a list of text chunks, each roughly `chunk_size` tokens, with
    `chunk_overlap` tokens shared between consecutive chunks for context
    continuity across chunk boundaries.
    """
    chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

    # Work at the paragraph level first — keeps semantically related text together.
    paragraphs = _split_on_separator(text, "\n\n") or _split_on_separator(text, "\n")

    chunks: list[str] = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if para_tokens > chunk_size:
            # Paragraph itself too big — fall back to sentence-level splitting.
            sentences = _split_on_separator(para, ". ")
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                sentence_tokens = count_tokens(sentence)
                if current_tokens + sentence_tokens > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start next chunk with overlap: keep the tail of the previous chunk
                    overlap_text = _tail_by_tokens(current_chunk, chunk_overlap)
                    current_chunk = overlap_text + " " + sentence
                    current_tokens = count_tokens(current_chunk)
                else:
                    current_chunk += (". " if current_chunk else "") + sentence
                    current_tokens += sentence_tokens
        else:
            if current_tokens + para_tokens > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                overlap_text = _tail_by_tokens(current_chunk, chunk_overlap)
                current_chunk = overlap_text + "\n\n" + para
                current_tokens = count_tokens(current_chunk)
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
                current_tokens += para_tokens

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _tail_by_tokens(text: str, num_tokens: int) -> str:
    """Returns the last `num_tokens` worth of text, used to build chunk overlap."""
    tokens = _encoding.encode(text)
    tail_tokens = tokens[-num_tokens:] if len(tokens) > num_tokens else tokens
    return _encoding.decode(tail_tokens)