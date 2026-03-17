from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

# Project root: the directory containing the rag/ package
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root automatically (safe to call multiple times)
load_dotenv(_PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True)
class RagConfig:
    data_dir: Path
    docs_dir: Path
    collection_name: str
    embedding_model: str
    llm_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    max_distance: float
    enable_ocr: bool
    lexical_top_n: int
    lexical_min_hits: int
    qdrant_url: str
    qdrant_api_key: str
    supabase_url: str
    supabase_service_key: str
    supabase_storage_bucket: str
    supabase_storage_prefix: str
    groq_api_key: str
    groq_base_url: str


def load_config() -> RagConfig:
    default_data = _PROJECT_ROOT / "data"
    data_dir = Path(os.getenv("RAG_DATA_DIR", str(default_data)))
    docs_dir = Path(os.getenv("RAG_DOCS_DIR", str(data_dir / "docs")))

    return RagConfig(
        data_dir=data_dir,
        docs_dir=docs_dir,
        collection_name=os.getenv("RAG_COLLECTION", "ucu_docs"),
        embedding_model=os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2"),
        llm_model=os.getenv("GROQ_MODEL", os.getenv("RAG_LLM_MODEL", "llama-3.1-8b-instant")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "300")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "60")),
        top_k=int(os.getenv("RAG_TOP_K", "6")),
        max_distance=float(os.getenv("RAG_MAX_DISTANCE", "1.1")),
        enable_ocr=os.getenv("RAG_OCR_ENABLED", "false").lower() == "true",
        lexical_top_n=int(os.getenv("RAG_LEXICAL_TOP_N", "8")),
        lexical_min_hits=int(os.getenv("RAG_LEXICAL_MIN_HITS", "1")),
        qdrant_url=os.getenv("QDRANT_URL", "").strip(),
        qdrant_api_key=os.getenv("QDRANT_API_KEY", "").strip(),
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY", "").strip(),
        supabase_storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "").strip(),
        supabase_storage_prefix=os.getenv("SUPABASE_STORAGE_PREFIX", "").strip(),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com" ).strip(),
    )
