from .confidence import compute_confidence
from .ocr import OCREngine
from .section_detector import split_label_text
from .text_cleaner import clean_text


class OCRProcessor:

    def __init__(self):
        self.ocr = OCREngine()

    def process(self, image_path):

        ocr_output = self.ocr.extract_text(image_path)

        raw_text = ocr_output["raw_text"]
        ocr_conf = ocr_output["ocr_confidence"]

        cleaned = clean_text(raw_text)
        ingredients, nutrition = split_label_text(cleaned)

        confidence = compute_confidence(
            raw_text, ingredients, nutrition, ocr_conf
        )

        return {
            "raw_text": raw_text,
            "ingredients": ingredients,
            "nutrition_text": nutrition,
            "confidence": confidence
        }