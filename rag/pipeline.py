from __future__ import annotations

from typing import List, Tuple

from .config import RagConfig, load_config
from .embeddings import EmbeddingModel
from .fallback import build_fallback_response
from .generator import generate_answer
from .lexical_search import lexical_search
from .vector_store import RetrievedChunk, VectorStore


class RAGPipeline:
    def __init__(self, config: RagConfig | None = None) -> None:
        self.config = config or load_config()
        self.embedder = EmbeddingModel(self.config.embedding_model)
        self.store = VectorStore(
            self.config.chroma_dir,
            self.config.collection_name,
            self.embedder,
        )

    def retrieve(self, question: str) -> List[str]:
        """
        Combine semantic (vector) and lexical (keyword) search.
        Always returns context — never gates on a confidence score.
        """
        # 1) Semantic search from Chroma
        semantic_chunks = self.store.query(question, self.config.top_k)
        semantic_texts = [chunk.text for chunk in semantic_chunks]

        # 2) Lexical keyword search from text cache
        lexical_lines = lexical_search(question, self.config)
        lexical_texts = [line for line, _ in lexical_lines]

        # 3) Interleave: alternate between semantic and lexical results
        #    so the LLM always gets the best of both search methods
        seen = set()
        merged: List[str] = []
        si, li = 0, 0
        while len(merged) < 4 and (si < len(semantic_texts) or li < len(lexical_texts)):
            # Take one from semantic
            while si < len(semantic_texts) and len(merged) < 4:
                key = semantic_texts[si][:200]
                si += 1
                if key not in seen:
                    seen.add(key)
                    merged.append(semantic_texts[si - 1])
                    break
            # Take one from lexical
            while li < len(lexical_texts) and len(merged) < 4:
                key = lexical_texts[li][:200]
                li += 1
                if key not in seen:
                    seen.add(key)
                    merged.append(lexical_texts[li - 1])
                    break

        return merged

    def answer(self, question: str) -> str:
        context_chunks = self.retrieve(question)
        if not context_chunks:
            return build_fallback_response(question)
        return generate_answer(question, context_chunks, self.config.llm_model)
