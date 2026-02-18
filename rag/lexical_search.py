from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .config import RagConfig


STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "to", "for", "in", "on",
    "and", "or", "with", "what", "when", "where", "how", "does",
    "do", "i", "we", "you", "it", "this", "that", "be", "as", "by",
    "from", "about", "please", "me", "my", "can", "retrieve",
    "tell", "show", "get", "give", "at", "its", "has", "have",
    "not", "but", "all", "was", "were",
}

# Max characters per context window to avoid sending huge chunks to the LLM
_MAX_WINDOW_CHARS = 600

# Number of lines above/below a matching line to include as context window
_WINDOW = 5


def _extract_terms(question: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", question.lower())
    seen: set[str] = set()
    terms: List[str] = []
    for t in tokens:
        if t not in STOPWORDS and len(t) > 1 and t not in seen:
            seen.add(t)
            terms.append(t)
    return terms


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _iter_source_texts(config: RagConfig) -> Iterable[Tuple[Path, str]]:
    """Yield (source_path, full_text) from the text cache or raw files."""
    cache_dir = config.data_dir / "text_cache"
    if cache_dir.exists():
        for cache_file in cache_dir.iterdir():
            if cache_file.suffix.lower() == ".txt" and cache_file.is_file():
                yield cache_file, _read_text_file(cache_file)
    # Also read raw .txt/.md files from docs if they exist
    if config.docs_dir.exists():
        for doc_path in config.docs_dir.rglob("*"):
            if doc_path.is_file() and doc_path.suffix.lower() in {".txt", ".md"}:
                yield doc_path, _read_text_file(doc_path)


def lexical_search(
    question: str, config: RagConfig
) -> List[Tuple[str, Dict[str, object]]]:
    """
    Keyword search with context windows.

    For each document, find lines matching query terms and return a window
    of surrounding lines for context. This way the LLM receives enough
    context rather than isolated single lines.
    """
    terms = _extract_terms(question)
    if not terms:
        return []

    # (score, text_window, metadata)
    scored: List[Tuple[float, str, Dict[str, object]]] = []

    for source_path, text in _iter_source_texts(config):
        if not text:
            continue
        lines = text.splitlines()
        used_indices: set[int] = set()

        for i, line in enumerate(lines):
            normalized = re.sub(r"\s+", " ", line).strip().lower()
            if not normalized:
                continue
            hits = sum(1 for term in terms if term in normalized)
            if hits < config.lexical_min_hits:
                continue
            if i in used_indices:
                continue

            # Build a context window around the matching line
            start = max(0, i - _WINDOW)
            end = min(len(lines), i + _WINDOW + 1)
            window = "\n".join(
                ln for ln in lines[start:end] if ln.strip()
            )
            if not window.strip():
                continue
            # Cap window size so one long document doesn't dominate
            if len(window) > _MAX_WINDOW_CHARS:
                window = window[:_MAX_WINDOW_CHARS]

            # Mark used so we don't return overlapping windows
            for j in range(start, end):
                used_indices.add(j)

            # Score: line-level hits (most important) + window-level breadth
            unique_hits = sum(1 for term in terms if term in window.lower())
            score = (hits * 2) + unique_hits
            scored.append((score, window, {"source": str(source_path)}))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: config.lexical_top_n]
    return [(text, metadata) for _, text, metadata in top]
