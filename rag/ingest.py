from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .chunking import chunk_text
from .config import RagConfig, load_config
from .document_loaders import Document, load_documents
from .embeddings import EmbeddingModel
from .vector_store import VectorStore


def find_documents(docs_dir: Path) -> List[Path]:
    files: List[Path] = []
    for path in docs_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md"}:
            files.append(path)
    return files


def prepare_chunks(documents: List[Document], config: RagConfig) -> List[Document]:
    chunked_documents: List[Document] = []
    for doc in documents:
        chunks = chunk_text(doc.text, config.chunk_size, config.chunk_overlap)
        for chunk_index, chunk in enumerate(chunks, start=1):
            metadata = dict(doc.metadata)
            metadata["chunk"] = chunk_index
            chunked_documents.append(Document(text=chunk, metadata=metadata))
    return chunked_documents


def write_text_cache(documents: List[Document], config: RagConfig) -> None:
    cache_dir = config.data_dir / "text_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, list[str]] = {}
    for doc in documents:
        source = doc.metadata.get("source")
        if not source:
            continue
        by_source.setdefault(source, []).append(doc.text)
    for source, texts in by_source.items():
        stem = Path(source).stem
        cache_path = cache_dir / f"{stem}.txt"
        combined = "\n".join(texts)
        cache_path.write_text(combined, encoding="utf-8")


def ingest(config: RagConfig, reset: bool = False) -> int:
    config.docs_dir.mkdir(parents=True, exist_ok=True)
    config.chroma_dir.mkdir(parents=True, exist_ok=True)

    files = find_documents(config.docs_dir)
    if not files:
        raise FileNotFoundError(
            f"No documents found in {config.docs_dir}. "
            "Add PDFs or text files before ingesting."
        )

    documents = load_documents(files, enable_ocr=config.enable_ocr)
    write_text_cache(documents, config)
    chunked_documents = prepare_chunks(documents, config)

    embedder = EmbeddingModel(config.embedding_model)
    store = VectorStore(config.chroma_dir, config.collection_name, embedder)

    if reset:
        store.reset(config.collection_name)

    texts = [doc.text for doc in chunked_documents]
    metadatas = [doc.metadata for doc in chunked_documents]
    store.add_texts(texts, metadatas)

    return len(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into Chroma.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection before ingesting.",
    )
    args = parser.parse_args()

    config = load_config()
    total = ingest(config, reset=args.reset)
    print(f"Ingested {total} chunks into '{config.collection_name}'.")


if __name__ == "__main__":
    main()
