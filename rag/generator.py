from typing import Generator, List

import ollama


SYSTEM_PROMPT = (
    "You are an informational chatbot for Uganda Christian University (UCU). "
    "Answer the question accurately using ONLY the provided context. "
    "If the answer is in the context, state it clearly and concisely. "
    "If the context does not contain enough information, say so honestly."
)


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
    prompt = build_prompt(question, context_chunks)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"num_predict": 150, "temperature": 0.3},
    )
    return response["message"]["content"].strip()


def generate_answer_stream(
    question: str, context_chunks: List[str], model: str
) -> Generator[str, None, None]:
    """Stream tokens one by one for Gradio."""
    prompt = build_prompt(question, context_chunks)
    stream = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"num_predict": 150, "temperature": 0.3},
        stream=True,
    )
    partial = ""
    for chunk in stream:
        token = chunk["message"]["content"]
        partial += token
        yield partial
