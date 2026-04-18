import os
from dotenv import load_dotenv
import requests
import time
import base64
import io
from PIL import Image

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

CHAT_COMPLETIONS_URL = "https://router.huggingface.co/v1/chat/completions"
PRIMARY_VISION_MODEL = "Qwen/Qwen3-VL-8B-Instruct"
SECONDARY_VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"


def _detect_mime_type(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        fmt = (img.format or "JPEG").lower()
        if fmt == "jpg":
            fmt = "jpeg"
        return f"image/{fmt}"
    except Exception:
        return "image/jpeg"


def query_model(model_name, image_bytes, prompt):
    for attempt in range(3):
        try:
            # Build multimodal chat payload supported by HF router v1 endpoint.
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = _detect_mime_type(image_bytes)

            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
            }

            response = requests.post(
                CHAT_COMPLETIONS_URL,
                headers=headers,
                json=payload,
                timeout=120
            )

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type.lower():
                data = response.json()
            else:
                data = response.text

            # 🔥 handle loading
            if isinstance(data, dict) and "error" in data:
                if "loading" in data["error"].lower():
                    print("Model loading... retrying")
                    time.sleep(5)
                    continue
                else:
                    return f"HF_ERROR_{data['error']}"

            if response.status_code == 200:
                if isinstance(data, dict):
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "")
                return str(data)

            if isinstance(data, str):
                return f"HF_ERROR_status_{response.status_code}_{data[:300]}"
            return f"HF_ERROR_status_{response.status_code}_{str(data)[:300]}"

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(5)

    return "HF_ERROR"

def query_llava(image_bytes, prompt):
    res = query_model(PRIMARY_VISION_MODEL, image_bytes, prompt)
    if res.startswith("HF_ERROR"):
        return res.replace("HF_ERROR", "LLAVA_ERROR")
    return res

def query_huggingface(image_bytes, prompt):
    return query_model(SECONDARY_VISION_MODEL, image_bytes, prompt)
