import torch
import easyocr
import numpy as np
import cv2
import os

# 🔥 helps reduce CUDA fragmentation issues
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


# ===== PREPROCESS =====
def preprocess_image(path):
    img = cv2.imread(path)

    if img is None:
        raise ValueError(f"Image not found: {path}")

    h, w = img.shape[:2]
    max_dim = 1000

    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(
            img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
        )

    return img


# ===== OCR ENGINE =====
class OCREngine:
    def __init__(self):
        print("CUDA available:", torch.cuda.is_available())
        print("Using GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

        self.reader = easyocr.Reader(
            ['en'],
            gpu=True,
            detector=True,
            recognizer=True,
            verbose=False
        )


    def extract_text(self, image_path):

        torch.cuda.empty_cache()  # 🔥 prevent memory issues

        img = preprocess_image(image_path)

        try:
            results = self.reader.readtext(img)
        except RuntimeError as e:
            # 🔥 fallback to CPU if GPU OOM
            if "out of memory" in str(e).lower():
                print("⚠️ GPU OOM → switching to CPU")
                self.reader = easyocr.Reader(['en'], gpu=False)
                results = self.reader.readtext(img)
            else:
                raise e

        texts = []
        confidences = []

        for (bbox, text, prob) in results:
            text = text.strip()

            # 🔥 filter garbage OCR
            if len(text) < 2:
                continue

            texts.append(text)
            confidences.append(prob)

        raw_text = " ".join(texts)

        avg_conf = (
            sum(confidences) / len(confidences)
            if confidences else 0
        )

        return {
            "raw_text": raw_text,
            "ocr_confidence": round(avg_conf, 3)
        }