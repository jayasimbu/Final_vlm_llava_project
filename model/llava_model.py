import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration

from config.settings import DEVICE, MODEL_ID, TORCH_DTYPE, MOCK_INFERENCE

if MOCK_INFERENCE:
    processor = None
    model = None
else:
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = LlavaForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=TORCH_DTYPE,
        device_map="auto" if DEVICE == "cuda" else None,
    )

    if DEVICE != "cuda":
        model.to(DEVICE)

