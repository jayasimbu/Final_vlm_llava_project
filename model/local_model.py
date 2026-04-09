from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# load once (important)
# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"DEBUG: Using device: {device}")

processor = None
model = None

def load_local_model():
    global processor, model
    if processor is not None:
        return True
    try:
        print("DEBUG: Loading local BLIP model...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
        return True
    except Exception as e:
        print(f"ERROR: Could not load local model ({e})")
        return False

def generate(image, prompt):
    if not load_local_model():
        return "LOCAL_ERROR: Model not loaded"
    formatted_prompt = f"Question: {prompt} Answer:"
    inputs = processor(image, formatted_prompt, return_tensors="pt").to(device)
    out = model.generate(
        **inputs,
        max_new_tokens=20,
        do_sample=False,
        repetition_penalty=1.2
    )
    return processor.decode(out[0], skip_special_tokens=True)
