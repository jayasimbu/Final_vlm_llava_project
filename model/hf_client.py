import os
from dotenv import load_dotenv
import requests
import time
import base64

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

LLAVA_URL = "https://router.huggingface.co/hf-inference/models/llava-hf/llava-v1.6-mistral-7b-hf"
BLIP2_URL = "https://api-inference.huggingface.co/models/Salesforce/blip2-flan-t5-xl"

def query_model(url, image_bytes, prompt):
    for attempt in range(3):
        try:
            # 1. Base64 Encode the image
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            
            # 2. Format specifically if it's LLaVA to ensure it "sees" the image token
            if "llava" in url.lower():
                final_prompt = f"USER: <image>\n{prompt}\nASSISTANT:"
            else:
                final_prompt = prompt

            # 3. Build JSON payload
            payload = {
                "inputs": final_prompt,
                "image": image_b64
            }
            
            # 4. Send as JSON! (Fixes IncompleteRead errors)
            response = requests.post(
                url,
                headers=headers,
                json=payload,  
                timeout=120
            )

            data = response.json()

            # 🔥 handle loading
            if isinstance(data, dict) and "error" in data:
                if "loading" in data["error"].lower():
                    print("Model loading... retrying")
                    time.sleep(5)
                    continue
                else:
                    return f"HF_ERROR_{data['error']}"

            if response.status_code == 200:
                if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                    return data[0]["generated_text"]
                elif isinstance(data, dict) and "generated_text" in data:
                    return data["generated_text"]
                return str(data)

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(5)

    return "HF_ERROR"

def query_llava(image_bytes, prompt):
    res = query_model(LLAVA_URL, image_bytes, prompt)
    if res.startswith("HF_ERROR"):
        return res.replace("HF_ERROR", "LLAVA_ERROR")
    return res

def query_huggingface(image_bytes, prompt):
    return query_model(BLIP2_URL, image_bytes, prompt)
