"""Inference engine for image + question answering using LLaVA."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Iterable, List

import torch

from vlm_llava.config import settings
from vlm_llava.model.load_model import load_llava_components
from vlm_llava.prompts.templates import build_auto_extraction_prompt, build_prompt
from vlm_llava.utils.image_preprocess import preprocess_image

logger = logging.getLogger(__name__)


@dataclass
class VLMResponse:
    """Represent final answer payload for each question."""

    question: str
    answer: str
    explanation: str
    confidence: float


def _extract_answer_segment(decoded_text: str) -> str:
    """Extract answer segment and strip wrappers from generated text."""
    text = decoded_text.strip()
    if "Answer:" in text:
        text = text.split("Answer:", 1)[-1].strip()

    # Keep only the first meaningful line to avoid trailing explanation noise.
    first_line = text.splitlines()[0].strip() if text else ""
    cleaned = first_line.strip(" \t\n\r\"'`*#")
    return cleaned or "Not found"


def _normalize_amount(text: str) -> str:
    """Normalize currency-like values into compact readable form."""
    if text.lower() == "not found":
        return text

    compact = re.sub(r"\s+", " ", text).strip()
    amount_match = re.search(r"([₹$€£])\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", compact)
    if amount_match:
        return f"{amount_match.group(1)}{amount_match.group(2)}"
    return compact


def _normalize_date(text: str) -> str:
    """Normalize detected date into DD/MM/YYYY when possible."""
    if text.lower() == "not found":
        return text

    compact = re.sub(r"\s+", " ", text).strip()

    # Convert YYYY-MM-DD to DD/MM/YYYY for consistent demo output.
    ymd = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", compact)
    if ymd:
        year, month, day = ymd.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"

    dmy = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b", compact)
    if dmy:
        day, month, year = dmy.groups()
        if len(year) == 2:
            year = f"20{year}"
        return f"{int(day):02d}/{int(month):02d}/{year}"

    return compact


def _clean_answer(question: str, raw_answer: str) -> str:
    """Clean generated answer based on question intent and normalize basic formats."""
    cleaned = _extract_answer_segment(raw_answer)
    lowered_question = question.lower()

    if "amount" in lowered_question or "tax" in lowered_question:
        return _normalize_amount(cleaned)
    if "date" in lowered_question:
        return _normalize_date(cleaned)
    return cleaned


def _estimate_confidence(cleaned_answer: str) -> float:
    """Estimate confidence score from answer quality heuristics."""
    if cleaned_answer.lower() == "not found" or cleaned_answer.lower().startswith("error"):
        return 0.2

    score = 0.55
    if len(cleaned_answer) >= 3:
        score += 0.12
    if len(cleaned_answer) <= 40:
        score += 0.1
    if re.search(r"\d", cleaned_answer):
        score += 0.08
    if re.search(r"[₹$€£]", cleaned_answer):
        score += 0.08

    return round(min(score, 0.98), 2)


def _generate_text(image_path: str, prompt: str) -> str:
    """Run one model generation pass for image plus prompt and return decoded text."""
    processor, model = load_llava_components()
    image = preprocess_image(image_path)

    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {key: value.to(settings.device) for key, value in inputs.items()}

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=settings.max_new_tokens,
            temperature=settings.temperature,
            top_p=settings.top_p,
            do_sample=settings.temperature > 0,
            use_cache=True,
        )

    return processor.batch_decode(output_ids, skip_special_tokens=True)[0]


def _generate_single_answer(image_path: str, question: str, system_context: str | None = None) -> VLMResponse:
    """Generate one answer from a single image and question."""
    prompt = build_prompt(question, system_context=system_context)
    decoded_text = _generate_text(image_path=image_path, prompt=prompt)
    answer = _clean_answer(question=question, raw_answer=decoded_text)
    confidence = _estimate_confidence(answer)
    explanation = "Generated directly from image-grounded visual-language reasoning."
    return VLMResponse(question=question, answer=answer, explanation=explanation, confidence=confidence)


def generate_batch_responses(
    image_path: str,
    questions: Iterable[str],
    system_context: str | None = None,
) -> List[VLMResponse]:
    """Generate answers for multiple questions on the same image with validation and logging."""
    question_list = [q.strip() for q in questions if q and q.strip()]
    if not question_list:
        raise ValueError("At least one non-empty question is required.")

    logger.info("Running batch inference for %d question(s)", len(question_list))
    responses: List[VLMResponse] = []
    for question in question_list:
        try:
            logger.info("Inference input | image=%s | question=%s", image_path, question)
            responses.append(_generate_single_answer(image_path, question, system_context=system_context))
            logger.info("Inference output | question=%s | answer=%s", question, responses[-1].answer)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Inference failed for question: %s", question)
            responses.append(
                VLMResponse(
                    question=question,
                    answer="Error",
                    explanation=f"Inference failed: {exc}",
                    confidence=0.0,
                )
            )

    return responses


def _safe_json_loads(text: str) -> dict[str, Any] | None:
    """Try to parse JSON object from generated text, including fenced outputs."""
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(candidate[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _structured_from_batch(results: List[VLMResponse]) -> dict[str, Any]:
    """Map question-level answers into clean structured invoice keys."""
    structured: dict[str, Any] = {
        "invoice_number": "Not found",
        "total_amount": "Not found",
        "invoice_date": "Not found",
        "vendor": "Not found",
        "tax": "Not found",
    }

    confidences: list[float] = []
    for item in results:
        key = settings.question_to_key.get(item.question)
        if key:
            structured[key] = item.answer or "Not found"
            confidences.append(item.confidence)

    structured["confidence"] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    return structured


def generate_structured_invoice_data(
    image_path: str,
    system_context: str | None = None,
) -> dict[str, Any]:
    """Extract invoice fields in one-pass JSON mode with safe per-question fallback."""
    logger.info("Running auto extraction mode")
    auto_prompt = build_auto_extraction_prompt(system_context=system_context)

    try:
        raw_text = _generate_text(image_path=image_path, prompt=auto_prompt)
        logger.info("Auto extraction raw output: %s", raw_text)
        parsed = _safe_json_loads(raw_text)
        if parsed is not None:
            result = {
                "invoice_number": _clean_answer("invoice number", str(parsed.get("invoice_number", "Not found"))),
                "total_amount": _normalize_amount(str(parsed.get("total_amount", "Not found"))),
                "invoice_date": _normalize_date(str(parsed.get("invoice_date", "Not found"))),
                "vendor": _clean_answer("vendor", str(parsed.get("vendor", "Not found"))),
                "tax": _normalize_amount(str(parsed.get("tax", "Not found"))),
            }
            result["confidence"] = round(
                sum(_estimate_confidence(str(value)) for key, value in result.items() if key != "confidence") / 5,
                2,
            )
            logger.info("Auto extraction structured output: %s", result)
            return result
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("One-pass JSON extraction failed: %s", exc)

    # Fallback mode keeps the system robust when JSON generation is malformed.
    fallback_results = generate_batch_responses(
        image_path=image_path,
        questions=settings.predefined_questions,
        system_context=system_context,
    )
    return _structured_from_batch(fallback_results)
