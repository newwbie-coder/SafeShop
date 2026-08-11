import re
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .final_scoring_engine import final_score, get_verdict
from .ingredient_analyzer import analyze_ingredients
from .normalize_dataset import normalize_ingredients
from .nutrition_parser4 import parse_nutrition
from ocr_layer.section_detector import extract_ingredients, extract_nutrition
from ocr_layer.text_cleaner import clean_text as clean_ocr_text

app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductInput(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    nutrition_text: Optional[str] = ""
    ingredients: Optional[str] = ""


class RawTextInput(BaseModel):
    name: str
    raw_text: Optional[str] = ""


def get_health_flags(n):
    flags = []

    sugar = n.get("sugar_g", 0) or 0
    carbs = n.get("carbohydrate_g", 0) or 0
    sodium = n.get("sodium_mg", 0) or 0
    sat_fat = n.get("saturated_fat_g", 0) or 0
    trans_fat = n.get("trans_fat_g", 0) or 0
    energy = n.get("energy_kcal", 0) or 0

    if sugar > 10 or carbs > 60:
        flags.append({
            "type": "diabetes",
            "message": f"High sugar/carbs ({sugar}g sugar, {carbs}g carbs)"
        })

    if sodium > 500:
        flags.append({
            "type": "bp",
            "message": f"High sodium ({sodium}mg)"
        })

    if trans_fat > 0:
        flags.append({
            "type": "heart",
            "message": "Contains trans fat"
        })
    elif sat_fat > 10:
        flags.append({
            "type": "heart",
            "message": f"High saturated fat ({sat_fat}g)"
        })

    if energy > 400 or sugar > 20:
        flags.append({
            "type": "weight",
            "message": "High calorie/sugar"
        })

    return flags


def score_product(ingredients, nutrition_text):
    """Shared scoring pipeline used by both /analyze and /analyze_text.

    Accepts free-form ingredient text and nutrition text and returns the full
    SafeShop analysis payload. Keeping this in one place means the two entry
    points always produce an identical response shape.
    """
    raw_text = (ingredients or "").lower().strip()
    has_ingredients = bool(raw_text)

    if has_ingredients:
        ins_codes = re.findall(r"\b\d{3,4}\b", raw_text)
        ins_codes = [f"ins{code}" for code in ins_codes]

        raw_text = re.sub(r"\(.*?\)", "", raw_text)

        normalized_ingredients = normalize_ingredients(raw_text)
        normalized_ingredients.extend(ins_codes)
        normalized_ingredients = list(dict.fromkeys(normalized_ingredients))

        ingredient_analysis = analyze_ingredients(normalized_ingredients)

    else:
        normalized_ingredients = []
        ingredient_analysis = {
            "additives": {
                "primary": [],
                "secondary": [],
                "generic": []
            },
            "msg": False,
            "ultra_processed": False,
            "sweeteners": []
        }

    parsed_nutrition = parse_nutrition(nutrition_text)
    has_nutrition = parsed_nutrition.get("confidence", 0) > 0

    product_data = {
        "parsed_nutrition": parsed_nutrition,
        "ingredient_analysis": ingredient_analysis
    }

    score, reasons = final_score(product_data)
    health_flags = get_health_flags(parsed_nutrition)

    return {
        "score": round(score, 2),
        "verdict": get_verdict(score),
        "reasons": list(set(reasons)),
        "parsed_nutrition": parsed_nutrition,
        "health_flags": health_flags,
        "confidence": (
            parsed_nutrition.get("confidence", 0) * 0.6 +
            (1 if has_ingredients else 0) * 0.4
        ),
        "tokens": normalized_ingredients,
        "additives": ingredient_analysis.get("additives", {}),
        "flags": {
            "msg": ingredient_analysis.get("msg", False),
            "ultra_processed": ingredient_analysis.get("ultra_processed", False),
            "sweeteners": ingredient_analysis.get("sweeteners", [])
        },
        "data_quality": {
            "has_ingredients": has_ingredients,
            "has_nutrition": has_nutrition
        }
    }


@app.post("/analyze")
def analyze_product(product: ProductInput):
    return score_product(product.ingredients, product.nutrition_text)


@app.post("/analyze_text")
def analyze_text(payload: RawTextInput):
    """Analyze a raw OCR text blob (from the mobile camera/overlay capture).

    The phone sends whatever text it read off the screen or label; we clean it,
    split ingredient vs nutrition sections here, and reuse the same scorer.
    """
    cleaned = clean_ocr_text(payload.raw_text or "")
    ingredients = extract_ingredients(cleaned)
    nutrition = extract_nutrition(cleaned)

    result = score_product(ingredients, nutrition)
    result["extracted"] = {
        "ingredients": ingredients,
        "nutrition_text": nutrition
    }
    return result


@app.get("/")
def root():
    return {"message": "SafeShop API running"}
