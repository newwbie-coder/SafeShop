from .confidence import compute_confidence
from .ocr import OCREngine
from .section_detector import extract_ingredients, extract_nutrition
from .text_cleaner import clean_text


class OCRProcessor:

    def __init__(self):
        self.ocr = OCREngine()

    def process(self, image_path):

        # ===== 1. OCR =====
        ocr_output = self.ocr.extract_text(image_path)

        raw_text = ocr_output["raw_text"]
        ocr_conf = ocr_output["ocr_confidence"]

        # ===== 2. CLEAN =====
        cleaned = clean_text(raw_text)

        # ===== 3. SECTION DETECTION =====
        ingredients = extract_ingredients(cleaned)
        nutrition = extract_nutrition(cleaned)

        # ===== 4. CONFIDENCE =====
        confidence = compute_confidence(
            raw_text, ingredients, nutrition, ocr_conf
        )

        return {
            "raw_text": raw_text,
            "ingredients": ingredients,
            "nutrition_text": nutrition,
            "confidence": confidence
        }