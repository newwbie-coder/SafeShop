import json
from pathlib import Path

from .final_scoring_engine import final_score, get_verdict
from .ingredient_analyzer import analyze_ingredients
from .ingredient_cleaner import clean_ingredients
from .nutrition_parser4 import parse_nutrition as parse_fn


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "sample"
INPUT = DATA_DIR / "sample_products_normalized.jsonl"
OUTPUT = DATA_DIR / "sample_products_scored.jsonl"


def process_product(product):

    # ===== 1. INGREDIENT CLEANING =====
    raw_ingredients = product.get("ingredients", [])
    if isinstance(raw_ingredients, str):
        raw_ingredients = [item.strip() for item in raw_ingredients.split(",") if item.strip()]
    elif not isinstance(raw_ingredients, list):
        raw_ingredients = []
    cleaned_ingredients = clean_ingredients(raw_ingredients)

    # convert list → string for analyzer
    ingredient_text = " ".join(cleaned_ingredients)

    # ===== 2. INGREDIENT ANALYSIS =====
    ingredient_analysis = analyze_ingredients(ingredient_text)

    # ===== 3. NUTRITION PARSING =====
    nutrition_text = product.get("nutrition", "")

    try:
        parsed_nutrition = parse_fn(nutrition_text)
    except TypeError:
        # fallback if parser expects (text, existing)
        parsed_nutrition = parse_fn(nutrition_text, {})

    # ===== 4. SCORING =====
    product["ingredients"] = cleaned_ingredients
    product["ingredient_analysis"] = ingredient_analysis
    product["parsed_nutrition"] = parsed_nutrition

    score, reasons = final_score(product)

    product["health_score"] = score
    product["verdict"] = get_verdict(score)
    product["reasons"] = list(set(reasons))

    return product


def run_pipeline():
    count = 0
    errors = 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open("r", encoding="utf-8") as infile, \
         OUTPUT.open("w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                product = json.loads(line)
            except Exception:
                continue

            try:
                processed = process_product(product)
                outfile.write(json.dumps(processed, ensure_ascii=False) + "\n")
                count += 1
            except Exception as e:
                errors += 1
                print("Error:", e)

    print(f"\nPipeline complete: {count} products processed")
    print(f"Errors: {errors}")
    print(f"Output saved to: {OUTPUT}")


if __name__ == "__main__":
    run_pipeline()
