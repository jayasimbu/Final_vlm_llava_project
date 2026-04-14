import base64
import logging
import os
import time

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

LLAVA_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
LLAVA_MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"

def query_llava(image_bytes: bytes, prompt: str) -> str:
    """Query LLaVA model via Hugging Face API with image and text prompt.
    
    Implements exponential backoff retry logic (3 attempts with 5s delays).
    
    Args:
        image_bytes: Image data as bytes
        prompt: Text prompt for the model
        
    Returns:
        Model response or error string prefixed with 'LLAVA_ERROR'
    """
    for attempt in range(3):
        try:
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": LLAVA_MODEL_ID,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                        ]
                    }
                ],
                "max_tokens": 256,
                "temperature": 0.1
            }

            response = requests.post(
                LLAVA_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=120
            )

            data = response.json()

            if response.status_code != 200:
                err_msg = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
                return f"LLAVA_ERROR_{err_msg}"

            choices = data.get("choices", []) if isinstance(data, dict) else []
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")

            return "LLAVA_ERROR_Empty response"

        except Exception as e:
            logger.error(f"LLaVA request failed (attempt {attempt + 1}/3): {e}")
            time.sleep(5)

    return "LLAVA_ERROR"
