"""Model loader for LLaVA tokenizer/processor/model."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Tuple

from transformers import AutoProcessor, LlavaForConditionalGeneration

from vlm_llava.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_llava_components() -> Tuple[AutoProcessor, LlavaForConditionalGeneration]:
    """Load and cache the LLaVA processor and model with optimal precision/device."""
    logger.info("Loading processor and model: %s", settings.model_name)

    processor = AutoProcessor.from_pretrained(settings.model_name)
    model = LlavaForConditionalGeneration.from_pretrained(
        settings.model_name,
        torch_dtype=settings.torch_dtype,
        low_cpu_mem_usage=True,
    )

    model.to(settings.device)
    model.eval()

    logger.info("Model loaded successfully on device: %s", settings.device)
    return processor, model
