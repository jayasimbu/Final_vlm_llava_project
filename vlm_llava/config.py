"""Central configuration for the VLM (LLaVA) module."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import torch


@dataclass(frozen=True)
class Settings:
    """Store all runtime settings for model loading and generation."""

    model_name: str = os.getenv("VLM_MODEL_NAME", "llava-hf/llava-1.5-7b-hf")
    max_new_tokens: int = int(os.getenv("VLM_MAX_NEW_TOKENS", "192"))
    temperature: float = float(os.getenv("VLM_TEMPERATURE", "0.1"))
    top_p: float = float(os.getenv("VLM_TOP_P", "0.85"))
    image_size: int = int(os.getenv("VLM_IMAGE_SIZE", "768"))
    log_file: str = os.getenv("VLM_LOG_FILE", "logs/app.log")

    predefined_questions: tuple[str, ...] = (
        "What is the invoice number?",
        "What is the total amount?",
        "What is the invoice date?",
        "Who is the vendor?",
        "What is the tax amount?",
    )

    question_to_key: dict[str, str] = field(
        default_factory=lambda: {
            "What is the invoice number?": "invoice_number",
            "What is the total amount?": "total_amount",
            "What is the invoice date?": "invoice_date",
            "Who is the vendor?": "vendor",
            "What is the tax amount?": "tax",
        }
    )

    @property
    def device(self) -> str:
        """Choose CUDA when available, else CPU."""
        return "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def torch_dtype(self) -> torch.dtype:
        """Use fp16 on GPU for memory and speed; fp32 on CPU for safety."""
        return torch.float16 if self.device == "cuda" else torch.float32


settings = Settings()
