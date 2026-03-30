"""Image preprocessing utilities for VLM input."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from vlm_llava.config import settings


def preprocess_image(image_path: str) -> Image.Image:
    """Load, validate, convert, and resize image into model-compatible RGB format."""
    if not image_path or not image_path.strip():
        raise ValueError("Image path cannot be empty.")

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not path.is_file():
        raise ValueError(f"Provided path is not a file: {image_path}")

    try:
        image = Image.open(path)
    except UnidentifiedImageError as exc:
        raise ValueError(f"Invalid image file: {image_path}") from exc

    # Convert to RGB and resize to a square size for predictable memory usage.
    image = image.convert("RGB")
    image = image.resize((settings.image_size, settings.image_size), Image.Resampling.LANCZOS)
    return image
