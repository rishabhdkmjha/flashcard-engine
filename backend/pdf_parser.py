import re
from pathlib import Path
from dataclasses import dataclass
import pdfplumber


@dataclass
class ContentChunk:
    text: str
    page_number: int
    chunk_index: int


def extract_text_chunks(pdf_path: Path, max_chunk_chars: int = 1800) -> list[ContentChunk]:
    raw_pages = _extract_pages(pdf_path)
    joined = _join_pages(raw_pages)
    chunks = _split_into_chunks(joined, max_chunk_chars)
    return chunks


def _extract_pages(pdf_path: Path) -> list[dict]:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"text": _clean_text(text), "page": page_number})
    return pages


def _clean_text(raw: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', raw)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\f', '\n\n', text)
    return text.strip()


def _join_pages(pages: list[dict]) -> list[tuple[str, int]]:
    return [(p["text"], p["page"]) for p in pages]


def _split_into_chunks(pages: list[tuple[str, int]], max_chars: int) -> list[ContentChunk]:
    chunks = []
    chunk_index = 0
    buffer = ""
    buffer_page = 1

    for text, page in pages:
        paragraphs = re.split(r'\n\n+', text)
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(buffer) + len(para) > max_chars and buffer:
                chunks.append(ContentChunk(
                    text=buffer.strip(),
                    page_number=buffer_page,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1
                buffer = para
                buffer_page = page
            else:
                buffer = (buffer + "\n\n" + para).strip()
                if not buffer:
                    buffer_page = page

    if buffer.strip():
        chunks.append(ContentChunk(
            text=buffer.strip(),
            page_number=buffer_page,
            chunk_index=chunk_index,
        ))

    return chunks
