from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pypdf import PdfReader


@dataclass
class Document:
    text: str
    metadata: Dict[str, Any]


def _document_title(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip()


def load_txt(path: Path) -> Document:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title = _document_title(path)
    combined = f"Document Title: {title}\n{text}"
    return Document(
        text=combined,
        metadata={
            "source": str(path),
            "title": title,
            "title_lower": title.lower(),
        },
    )


def load_pdf(path: Path, enable_ocr: bool = False) -> List[Document]:
    reader = PdfReader(str(path))
    title = _document_title(path)
    documents: List[Document] = []
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if not page_text:
            continue
        combined = f"Document Title: {title}\n{page_text}"
        documents.append(
            Document(
                text=combined,
                metadata={
                    "source": str(path),
                    "page": page_index,
                    "title": title,
                    "title_lower": title.lower(),
                },
            )
        )
    if not documents and enable_ocr:
        try:
            from .ocr import ocr_pdf

            for page_index, page_text in ocr_pdf(path):
                combined = f"Document Title: {title}\n{page_text}"
                documents.append(
                    Document(
                        text=combined,
                        metadata={
                            "source": str(path),
                            "page": page_index,
                            "ocr": True,
                            "title": title,
                            "title_lower": title.lower(),
                        },
                    )
                )
        except Exception as exc:
            print(f"OCR failed for {path}: {exc}")
    return documents


def load_documents(paths: Iterable[Path], enable_ocr: bool = False) -> List[Document]:
    documents: List[Document] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            documents.extend(load_pdf(path, enable_ocr=enable_ocr))
        elif suffix in {".txt", ".md"}:
            documents.append(load_txt(path))
    return documents
