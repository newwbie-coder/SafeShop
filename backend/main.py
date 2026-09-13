from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .catalog import lookup as catalog_lookup, remember as catalog_remember
from .feedback_store import record_feedback
from .final_scoring_engine import final_score, get_verdict
from .ingredient_analyzer import analyze_ingredients
from .normalize_dataset import normalize_ingredients
from .nutrition_parser4 import looks_like_ingredient_list, parse_nutrition
from ocr_layer.section_detector import split_label_text
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
    product_id: Optional[str] = None
    nutrition_text: Optional[str] = ""
    ingredients: Optional[str] = ""


class RawTextInput(BaseModel):
    name: str
    raw_text: Optional[str] = ""


class FeedbackInput(BaseModel):
    comment: str
    name: Optional[str] = None
    brand: Optional[str] = None
    product_id: Optional[str] = None
    score_shown: Optional[float] = None
    verdict_shown: Optional[str] = None


class ImageInput(BaseModel):
    name: Optional[str] = ""
    brand: Optional[str] = None
    product_id: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


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
    ingredients = ingredients or ""
    nutrition_text = nutrition_text or ""

    if (not ingredients.strip()) and looks_like_ingredient_list(nutrition_text):
        ingredients = nutrition_text
        nutrition_text = ""

    raw_text = ingredients.lower().strip()
    has_ingredients = bool(raw_text)

    if has_ingredients:
        normalized_ingredients = normalize_ingredients(ingredients)
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
        "ingredient_analysis": ingredient_analysis,
        "tokens": normalized_ingredients,
        "ingredients": normalized_ingredients,
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
        },
        "needs_ocr": (not has_ingredients) and (not has_nutrition),
    }


@app.post("/analyze")
def analyze_product(product: ProductInput):
    ingredients = product.ingredients or ""
    nutrition = product.nutrition_text or ""
    source = "live"

    cached = catalog_lookup(product.product_id, product.brand, product.name)
    if cached:
        if not ingredients.strip() and cached.get("ingredients"):
            ingredients = cached["ingredients"]
            source = "cache"
        if not nutrition.strip() and cached.get("nutrition"):
            nutrition = cached["nutrition"]
            source = "cache"

    result = score_product(ingredients, nutrition)
    result["source"] = source
    if cached:
        result["product_id"] = cached.get("product_id") or product.product_id
        if cached.get("name"):
            result["matched_name"] = cached.get("name")
    else:
        result["product_id"] = product.product_id

    if source == "live" and not result.get("needs_ocr"):
        catalog_remember(
            product.product_id,
            product.brand,
            product.name,
            ingredients,
            nutrition,
        )
    return result


@app.post("/analyze_text")
def analyze_text(payload: RawTextInput):
    """Analyze a raw OCR text blob (from the mobile camera/overlay capture).

    The phone sends whatever text it read off the screen or label; we clean it,
    split ingredient vs nutrition sections here, and reuse the same scorer.
    """
    cleaned = clean_ocr_text(payload.raw_text or "")
    ingredients, nutrition = split_label_text(cleaned)

    result = score_product(ingredients, nutrition)
    result["extracted"] = {
        "ingredients": ingredients,
        "nutrition_text": nutrition
    }
    result["source"] = "ocr_text"
    return result


@app.post("/analyze_image")
def analyze_image(payload: ImageInput):
    """OCR fallback when the product page has no ingredients/nutrition text."""
    try:
        from .image_fallback import ocr_label_image

        extracted = ocr_label_image(
            image_url=payload.image_url,
            image_base64=payload.image_base64,
        )
    except ImportError:
        return JSONResponse(
            {"error": True, "message": "OCR extras are not installed on this machine"},
            status_code=503,
        )
    except ValueError as exc:
        return JSONResponse({"error": True, "message": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": True, "message": f"OCR failed: {exc}"}, status_code=500)

    result = score_product(extracted.get("ingredients"), extracted.get("nutrition_text"))
    result["source"] = "ocr"
    result["extracted"] = extracted
    result["product_id"] = payload.product_id
    if payload.name and not result.get("needs_ocr"):
        catalog_remember(
            payload.product_id,
            payload.brand,
            payload.name,
            extracted.get("ingredients") or "",
            extracted.get("nutrition_text") or "",
        )
    return result


@app.post("/feedback")
def submit_feedback(payload: FeedbackInput):
    row = record_feedback(
        comment=payload.comment,
        name=payload.name,
        brand=payload.brand,
        product_id=payload.product_id,
        score_shown=payload.score_shown,
        verdict_shown=payload.verdict_shown,
    )
    return {"ok": True, "stored": row}


@app.get("/")
def root():
    return {"message": "SafeShop API running"}
