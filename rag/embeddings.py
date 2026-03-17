from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()
