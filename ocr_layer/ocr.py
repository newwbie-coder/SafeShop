import torch
import easyocr
import numpy as np
import cv2
import os

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


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


class OCREngine:
    def __init__(self):
        use_gpu = torch.cuda.is_available()
        print("CUDA available:", use_gpu)
        if use_gpu:
            print("Using GPU:", torch.cuda.get_device_name(0))
        else:
            print("Using GPU: CPU")

        self.reader = easyocr.Reader(
            ["en"],
            gpu=use_gpu,
            detector=True,
            recognizer=True,
            verbose=False,
        )

    def extract_text(self, image_path):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        img = preprocess_image(image_path)

        try:
            results = self.reader.readtext(img)
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print("GPU OOM -> switching to CPU")
                self.reader = easyocr.Reader(["en"], gpu=False)
                results = self.reader.readtext(img)
            else:
                raise e

        texts = []
        confidences = []

        for (bbox, text, prob) in results:
            text = text.strip()
            if len(text) < 2:
                continue
            texts.append(text)
            confidences.append(prob)

        raw_text = " ".join(texts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        return {
            "raw_text": raw_text,
            "ocr_confidence": round(avg_conf, 3),
        }
