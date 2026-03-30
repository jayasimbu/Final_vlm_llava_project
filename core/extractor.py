from core.prompt import get_prompt
from config.settings import DEVICE, MAX_TOKENS


def extract_data(image):
    # Defer model import so endpoints that fail validation early do not load model deps.
    from model.llava_model import model, processor

    prompt = get_prompt()

    inputs = processor(text=prompt, images=image, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    output = model.generate(**inputs, max_new_tokens=MAX_TOKENS)
    result = processor.decode(output[0], skip_special_tokens=True)

    return result
