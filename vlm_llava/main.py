"""CLI entry point for VLM (LLaVA) image-based question answering."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import List

from vlm_llava.config import settings
from vlm_llava.inference.generate_response import generate_batch_responses, generate_structured_invoice_data


def configure_logging() -> None:
    """Configure consistent console logging for operational visibility."""
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def collect_questions(raw_input: str) -> List[str]:
    """Parse semicolon-separated questions into a clean list."""
    return [item.strip() for item in raw_input.split(";") if item.strip()]


def main() -> int:
    """Run interactive CLI flow and print answers in a clean format."""
    configure_logging()

    try:
        image_path = input("Enter image path: ").strip()
        if not image_path:
            raise ValueError("Image path is required.")

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        print("\nSelect Mode:")
        print("1 - Manual प्रश्न")
        print("2 - Auto Invoice Extraction")
        mode = input("Enter mode number: ").strip()
        logging.info("CLI input | image=%s | mode=%s", image_path, mode)

        if mode == "2":
            result = generate_structured_invoice_data(image_path=image_path)
            logging.info("Auto extraction completed for image: %s", image_path)
            print("\n===== Structured Invoice JSON =====")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if mode != "1":
            raise ValueError("Invalid mode selected. Choose 1 or 2.")

        raw_questions = input("Enter question(s) separated by ';': ").strip()
        questions = collect_questions(raw_questions)
        if not questions:
            raise ValueError("At least one question is required.")
        logging.info("Manual mode questions: %s", questions)

        system_context = input("Optional system prompt override (or press Enter): ").strip()
        if not system_context:
            system_context = None

        results = generate_batch_responses(
            image_path=image_path,
            questions=questions,
            system_context=system_context,
        )

        print("\n===== VLM Results =====")
        for item in results:
            print(f"\nQuestion: {item.question}")
            print(f"Answer: {item.answer}")
            print(f"Explanation: {item.explanation}")
            print(f"Confidence: {item.confidence}")

        return 0

    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Application failed")
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
