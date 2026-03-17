# RAG Chatbot (New Implementation)

This folder contains the Retrieval-Augmented Generation (RAG) upgrade for the
university chatbot. It is separate from the legacy zero-shot version in
`Notebooks/`.

## What This Adds

- Document ingestion (PDF, TXT, MD) into a vector database
- Semantic retrieval using Qdrant Cloud
- Hosted LLM generation via Groq API
- Supabase Storage sync for source documents
- Flask web UI in `web/`

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r ../requirements_rag.txt
   ```

2. Upload documents to Supabase Storage bucket (`SUPABASE_STORAGE_BUCKET`) and/or add local documents to `../data/docs/`.

3. Ingest documents:
   ```bash
   python -m rag.ingest
   ```

4. Run the web UI:
   ```bash
   python ../web/app.py
   ```

## Project Structure

- `config.py` — configuration and environment variables
- `document_loaders.py` — load PDFs and text files
- `chunking.py` — split documents into overlapping chunks
- `embeddings.py` — sentence-transformer embeddings
- `vector_store.py` — Qdrant vector database wrapper
- `generator.py` — Groq LLM generation
- `pipeline.py` — retrieval + generation pipeline
- `ingest.py` — command-line ingestion pipeline + Supabase Storage sync

## Environment Variables (Optional)

- `RAG_DATA_DIR` (default: `data`)
- `RAG_DOCS_DIR` (default: `data/docs`)
- `RAG_COLLECTION` (default: `ucu_docs`)
- `RAG_EMBED_MODEL` (default: `all-MiniLM-L6-v2`)
- `GROQ_API_KEY` (required)
- `GROQ_MODEL` (default: `llama-3.1-8b-instant`)
- `GROQ_BASE_URL` (optional override)
- `QDRANT_URL` (required)
- `QDRANT_API_KEY` (required for private clusters)
- `SUPABASE_URL` (required for storage sync)
- `SUPABASE_SERVICE_KEY` (required for storage sync)
- `SUPABASE_STORAGE_BUCKET` (required for storage sync)
- `SUPABASE_STORAGE_PREFIX` (optional)
- `RAG_CHUNK_SIZE` (default: `300` words)
- `RAG_CHUNK_OVERLAP` (default: `60` words)
- `RAG_TOP_K` (default: `6`)
- `RAG_MAX_DISTANCE` (default: `1.1`)
- `RAG_OCR_ENABLED` (default: `false`)
- `RAG_LEXICAL_TOP_N` (default: `8`)
- `RAG_LEXICAL_MIN_HITS` (default: `1`)

## Notes

- Groq API key must be configured.
- If you re-ingest, use `python -m rag.ingest --reset` to clear the Qdrant collection.
- When retrieval confidence is low, the chatbot returns a human fallback response.

## OCR (Scanned PDFs)

If your PDFs are scanned images, enable OCR so text can be indexed:

```bash
sudo apt install -y tesseract-ocr poppler-utils
pip install -r ../requirements_rag.txt
export RAG_OCR_ENABLED=true
python -m rag.ingest --reset
```
