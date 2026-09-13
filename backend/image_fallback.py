"""Optional image-label OCR. Imported lazily so /analyze works without EasyOCR."""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_HOST_SUFFIXES = (
    "bbassets.com",
    "bigbasket.com",
    "localhost",
    "127.0.0.1",
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
_ENGINE = None


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)


def _write_bytes(data: bytes) -> str:
    handle = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    handle.write(data)
    handle.close()
    return handle.name


def _get_engine():
    global _ENGINE
    if _ENGINE is None:
        from ocr_layer.ocr import OCREngine

        _ENGINE = OCREngine()
    return _ENGINE


def load_image_bytes(image_url: str | None = None, image_base64: str | None = None) -> str:
    if image_base64:
        payload = image_base64.split(",", 1)[-1]
        return _write_bytes(base64.b64decode(payload))
    if image_url:
        if not _host_allowed(image_url):
            raise ValueError("Image host is not allowed")
        req = Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 SafeShop/1.0",
                "Referer": "https://www.bigbasket.com/",
            },
        )
        with urlopen(req, timeout=8) as response:
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Image is too large")
        if len(data) < 32:
            raise ValueError("Image was empty")
        return _write_bytes(data)
    raise ValueError("Provide image_url or image_base64")


def ocr_label_image(image_url: str | None = None, image_base64: str | None = None) -> dict:
    from ocr_layer.confidence import compute_confidence
    from ocr_layer.section_detector import split_label_text
    from ocr_layer.text_cleaner import clean_text

    path = load_image_bytes(image_url, image_base64)
    try:
        extracted = _get_engine().extract_text(path)
        raw_text = extracted["raw_text"]
        cleaned = clean_text(raw_text)
        ingredients, nutrition = split_label_text(cleaned)
        confidence = compute_confidence(
            raw_text, ingredients, nutrition, extracted["ocr_confidence"]
        )
        return {
            "raw_text": raw_text,
            "ingredients": ingredients,
            "nutrition_text": nutrition,
            "ocr_confidence": extracted["ocr_confidence"],
            "confidence": confidence,
        }
    finally:
        Path(path).unlink(missing_ok=True)
