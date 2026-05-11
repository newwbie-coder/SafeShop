import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "sample"
INPUT = DATA_DIR / "sample_products_normalized.jsonl"
OUTPUT = DATA_DIR / "sample_products_parsed.jsonl"


# ===== NORMALIZE =====
def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace(":", " ")

    return text


# ===== SAFE FLOAT =====
def safe_float(val):
    try:
        if "%" in str(val):
            return None
        val = str(val).replace("<", "").strip()
        return float(val)
    except:
        return None


# ===== STRICT (PRIMARY) =====
def extract_strict(keyword, text, unit):

    # normal case
    pattern1 = rf"{keyword}[^0-9]*([<]?[0-9]+\.?[0-9]*)\s*{unit}"
    match1 = re.search(pattern1, text)

    if match1:
        return safe_float(match1.group(1))

    # 🔥 KEY FIX: handles "Energy (kcal): 425"
    pattern2 = rf"{keyword}[^0-9]*\(?{unit}\)?[^0-9]*([<]?[0-9]+\.?[0-9]*)"
    match2 = re.search(pattern2, text)

    if match2:
        return safe_float(match2.group(1))

    return None


# ===== LABEL BASED =====
def extract_label(keyword, text):
    pattern = rf"{keyword}[^0-9]*([<]?[0-9]+\.?[0-9]*)"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group(1))
    return None


# ===== LOOSE FALLBACK =====
def extract_loose_all(text):
    return re.findall(r"([a-z\s]+?)\s*([<]?[0-9]+\.?[0-9]*)\s*(kcal|g|mg)", text)


# ===== CLEAN VALUE =====
def clean_value(val, key):

    if val is None:
        return None

    # sanity filters
    if key == "carbohydrate_g" and val > 150:
        return None
    if key == "protein_g" and val > 100:
        return None
    if key == "fat_g" and val > 100:
        return None

    return val


# ===== MAIN PARSER =====
def parse_nutrition(text):

    if not text or str(text).strip() == "0":
        return {}

    raw_text = text
    text = normalize(text)

    data = {
        "energy_kcal": None,
        "protein_g": None,
        "carbohydrate_g": None,
        "sugar_g": None,
        "added_sugar_g": None,
        "fat_g": None,
        "saturated_fat_g": None,
        "trans_fat_g": None,
        "fiber_g": None,
        "sodium_mg": None
    }

    # ===== 1. STRICT =====
    data["energy_kcal"] = extract_strict("energy|calories", text, "kcal")
    data["protein_g"] = extract_strict("protein", text, "g")
    data["carbohydrate_g"] = extract_strict("carbohydrate|carbs", text, "g")
    data["fat_g"] = extract_strict("fat", text, "g")

    # 🔥 FIXED sugar logic
    data["added_sugar_g"] = extract_strict("added sugars?", text, "g")
    data["sugar_g"] = extract_strict("total sugars?|sugars?", text, "g")

    data["saturated_fat_g"] = extract_strict("saturated", text, "g")
    data["trans_fat_g"] = extract_strict("trans", text, "g")
    data["fiber_g"] = extract_strict("(fibre|fiber|dietary fibre)", text, "g")

    sodium = extract_strict("sodium", text, "mg")
    salt = extract_strict("salt", text, "g")

    if sodium:
        data["sodium_mg"] = sodium
    elif salt:
        data["sodium_mg"] = salt * 400

    # ===== 2. LABEL FALLBACK =====
    for key, keyword in [
        ("energy_kcal", "energy"),
        ("protein_g", "protein"),
        ("carbohydrate_g", "carbohydrate"),
    ]:
        if not data[key]:
            data[key] = extract_label(keyword, text)

    # ===== 3. LOOSE FALLBACK =====
    matches = extract_loose_all(text)

    for label, value, unit in matches:

        value = safe_float(value)
        if value is None:
            continue

        label = label.strip()

        if not data["energy_kcal"] and ("energy" in label or "calorie" in label) and unit == "kcal":
            data["energy_kcal"] = value

        elif not data["protein_g"] and "protein" in label:
            data["protein_g"] = value

        elif not data["carbohydrate_g"] and ("carbohydrate" in label or "carb" in label):
            data["carbohydrate_g"] = value

        elif not data["added_sugar_g"] and "added sugar" in label:
            data["added_sugar_g"] = value

        elif not data["sugar_g"] and "sugar" in label:
            data["sugar_g"] = value

        elif not data["saturated_fat_g"] and "saturated" in label:
            data["saturated_fat_g"] = value

        elif not data["trans_fat_g"] and "trans" in label:
            data["trans_fat_g"] = value

        elif not data["fat_g"] and "fat" in label:
            data["fat_g"] = value

        elif not data["fiber_g"] and ("fiber" in label or "fibre" in label):
            data["fiber_g"] = value

        elif not data["sodium_mg"] and "sodium" in label:
            data["sodium_mg"] = value

        elif not data["sodium_mg"] and "salt" in label:
            data["sodium_mg"] = value * 400

    # ===== CLEAN =====
    for k in data:
        data[k] = clean_value(data[k], k)

    # sodium correction
    if data["sodium_mg"] and data["sodium_mg"] < 10:
        data["sodium_mg"] *= 1000

    # ===== CONFIDENCE =====
    essential = ["energy_kcal", "protein_g", "carbohydrate_g", "fat_g"]
    found = sum(1 for k in essential if data.get(k) is not None)

    data["confidence"] = round(found / len(essential), 2)

    data["raw_text"] = raw_text

    return data


# ===== MAIN =====
if __name__ == "__main__":
    count = 0
    low_conf = 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open("r", encoding="utf-8") as infile, \
         OUTPUT.open("w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                product = json.loads(line)
            except Exception:
                continue

            text = product.get("nutrition", "")

            parsed = parse_nutrition(text)

            product["parsed_nutrition"] = parsed

            if parsed.get("confidence", 0) < 0.5 and parsed:
                low_conf += 1

            outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
            count += 1

    print("\nPatched parser complete")
    print("Total:", count)
    print("Low confidence:", low_conf)