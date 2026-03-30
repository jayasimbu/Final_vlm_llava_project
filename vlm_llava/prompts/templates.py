"""Prompt templates for consistent invoice/receipt QA behavior."""

from __future__ import annotations


def build_prompt(question: str, system_context: str | None = None) -> str:
    """Build a structured prompt with optional custom system context."""
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    base_context = (
        system_context.strip()
        if system_context and system_context.strip()
        else (
            "You are a professional invoice analyst AI.\n\n"
            "Carefully analyze the given invoice image and extract accurate information.\n\n"
            "Rules:\n"
            "- Always give precise answers\n"
            "- Include currency for amounts\n"
            "- If information is missing, return 'Not found'\n"
            "- Do not hallucinate\n"
            "- Keep answers concise and structured"
        )
    )

    return (
        f"{base_context}\n"
        "If the answer is not present in the image, reply exactly: Not found\n"
        f"Question: {question.strip()}\n"
        "Answer:"
    )


def build_auto_extraction_prompt(system_context: str | None = None) -> str:
    """Build one-shot extraction prompt that requests structured JSON fields."""
    base_context = (
        system_context.strip()
        if system_context and system_context.strip()
        else (
            "You are a professional invoice analyst AI.\n\n"
            "Carefully analyze the given invoice image and extract accurate information.\n\n"
            "Rules:\n"
            "- Always give precise answers\n"
            "- Include currency for amounts\n"
            "- If information is missing, return 'Not found'\n"
            "- Do not hallucinate\n"
            "- Keep answers concise and structured"
        )
    )

    return (
        f"{base_context}\n"
        "Return only valid JSON with this exact schema and no extra text:\n"
        '{"invoice_number":"...","total_amount":"...","invoice_date":"...","vendor":"...","tax":"..."}'
    )
