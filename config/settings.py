import os

import torch

MODEL_ID = os.getenv("MODEL_ID", "llava-hf/llava-1.5-7b-hf")
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TORCH_DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
MOCK_INFERENCE = os.getenv("MOCK_INFERENCE", "True" if DEVICE == "cpu" else "False").lower() in ("true", "1")

