# Gamma Chatbot Project

This repository contains two versions of the university chatbot:

1. **Legacy zero-shot chatbot (December baseline)**  
   Located in `Notebooks/`. It uses intent matching with sentence-transformers and a
   Streamlit interface.

2. **RAG-based chatbot (new implementation)**  
   Located in `rag/` and `web/`. It uses document retrieval with Chroma and a local
   LLM (Ollama) plus a Flask app.

## RAG Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements_rag.txt
   ```

2. Add documents (PDF, TXT, MD) to `data/docs/`.

3. Ingest documents into Chroma:
   ```bash
   python -m rag.ingest
   ```

4. Run the web app:
   ```bash
   python web/app.py
   ```

## Environment Variables (optional)

- `RAG_DATA_DIR` (default: `data`)
- `RAG_DOCS_DIR` (default: `data/docs`)
- `RAG_CHROMA_DIR` (default: `data/chroma`)
- `RAG_COLLECTION` (default: `ucu_docs`)
- `RAG_EMBED_MODEL` (default: `all-MiniLM-L6-v2`)
- `RAG_LLM_MODEL` (default: `mistral`)
- `RAG_CHUNK_SIZE` (default: `300` words)
- `RAG_CHUNK_OVERLAP` (default: `60` words)
- `RAG_TOP_K` (default: `4`)
- `RAG_MAX_DISTANCE` (default: `1.1`)
- `RAG_OCR_ENABLED` (default: `false`)
- `RAG_LEXICAL_TOP_N` (default: `6`)
- `RAG_LEXICAL_MIN_HITS` (default: `1`)

## OCR (for scanned PDFs)

Some PDFs are scanned images and contain no selectable text. Enable OCR if you
need those documents indexed:

```bash
sudo apt install -y tesseract-ocr poppler-utils
pip install -r requirements_rag.txt
export RAG_OCR_ENABLED=true
python -m rag.ingest --reset
```

## WhatsApp Business API (Infobip)

The Flask app includes WhatsApp webhook integration via Infobip.

Set environment variables before starting the app:

```bash
export INFOBIP_BASE_URL="jr3qdk.api.infobip.com"
export INFOBIP_API_KEY="<your-infobip-api-key>"
export INFOBIP_WHATSAPP_SENDER="<your-whatsapp-sender-number>"
# optional shared secret for webhook protection
export INFOBIP_WEBHOOK_TOKEN="<random-shared-secret>"
```

Available endpoints:

- `GET /api/whatsapp/status` — quick health/config check
- `POST /webhooks/infobip/whatsapp` — inbound WhatsApp webhook from Infobip

Flow:

1. Infobip sends inbound WhatsApp text to `/webhooks/infobip/whatsapp`.
2. The app runs the RAG pipeline to generate an answer.
3. The app sends the answer back to the same number through Infobip.

Security note:

- Keep API keys in environment variables only.
- Rotate any key that has been shared in chat/history.

