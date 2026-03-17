import os
from typing import Generator, List

from groq import Groq


SYSTEM_PROMPT = (
    "You are an informational chatbot for Uganda Christian University (UCU). "
    "Answer the question accurately using ONLY the provided context. "
    "If the answer is in the context, state it clearly and concisely. "
    "If the context does not contain enough information, say so honestly."
)


def _build_groq_client(api_key: str) -> Groq:
    raw_base_url = os.getenv("GROQ_BASE_URL", "").strip()
    if not raw_base_url:
        return Groq(api_key=api_key)

    normalized = raw_base_url.rstrip("/")
    if normalized.endswith("/openai/v1"):
        normalized = normalized[: -len("/openai/v1")]

    return Groq(api_key=api_key, base_url=normalized)


def build_prompt(question: str, context_chunks: List[str]) -> str:
    context_text = "\n\n".join(
        f"[Context {idx + 1}]\n{chunk}" for idx, chunk in enumerate(context_chunks)
    )
    return (
        f"{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer concisely based on the context above:"
    )


def generate_answer(question: str, context_chunks: List[str], model: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required for answer generation.")

    prompt = build_prompt(question, context_chunks)
    client = _build_groq_client(api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=220,
    )
    return (response.choices[0].message.content or "").strip()


def generate_answer_stream(
    question: str, context_chunks: List[str], model: str
) -> Generator[str, None, None]:
    """Stream tokens one by one."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required for answer generation.")

    prompt = build_prompt(question, context_chunks)
    client = _build_groq_client(api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=220,
        stream=True,
    )
    partial = ""
    for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if not token:
            continue
        partial += token
        yield partial
