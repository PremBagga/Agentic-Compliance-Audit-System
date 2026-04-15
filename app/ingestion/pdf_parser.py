from __future__ import annotations

from io import BytesIO
from pathlib import Path


def _decode_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore").strip()


def parse_document_bytes(filename: str, file_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
            text = "\n".join(pages).strip()
            return text or _decode_bytes(file_bytes)
        except Exception:
            return _decode_bytes(file_bytes)

    if suffix in {".txt", ".md", ".csv", ".log", ""}:
        return _decode_bytes(file_bytes)

    return _decode_bytes(file_bytes)
