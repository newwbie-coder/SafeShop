import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "sample"
INPUT = DATA_DIR / "sample_products_normalized.jsonl"
OUTPUT = DATA_DIR / "sample_products_parsed.jsonl"


def looks_like_ingredient_list(text: str) -> bool:
    """True when a 'nutrition' blob is actually an ingredients sentence."""
    if not text:
        return False
    t = text.lower()
    has_panel = bool(re.search(r"\b(kcal|energy|protein|carbohydrate|sodium)\b", t))
    has_additive_language = bool(
        re.search(r"\b(ins\s*\d{3}|emulsifier|thickener|liquid glucose|flavouring)\b", t)
    )
    return has_additive_language and not has_panel


def detect_basis_g(raw_text: str):
    """Return grams/ml the panel is based on, or None if unknown (per-serve)."""
    if not raw_text:
        return 100.0
    t = raw_text.lower().replace("\n", " ")

    if re.search(r"per\s*100\s*(g|ml)\b", t) or re.search(
        r"nutrition[_\s]*per\s*[:\s]*100\s*(g|ml)", t
    ):
        return 100.0

    m = re.search(r"nutrition[_\s]*per\s*[:\s]*([0-9]+\.?[0-9]*)\s*(g|ml)", t)
    if m:
        val = float(m.group(1))
        if val > 0:
            return val

    if re.search(r"per\s*serv", t) and not re.search(r"per\s*100", t):
        m = re.search(r"serving[_\s]*size\s*[:\s]*([0-9]+\.?[0-9]*)\s*(g|ml)", t)
        if m:
            return float(m.group(1))
        return None

    m = re.search(r"serving[_\s]*size\s*[:\s]*([0-9]+\.?[0-9]*)\s*(g|ml)", t)
    if m and not re.search(r"per\s*100", t):
        val = float(m.group(1))
        if 0 < val < 80:
            return val

    return 100.0


def normalize(text):
    text = text.lower()
    text = text.replace("\n", " ")
    text = text.replace(",", " ")
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace(":", " ")

    text = re.sub(r"(per\s+)?100\s*(g|ml|mg|kcal)", " ", text)
    text = re.sub(r"approx.*?value", " ", text)
    text = re.sub(r"based on \d+\s*kcal", " ", text)
    text = re.sub(r"\d+\s*kcal diet", " ", text)
    text = re.sub(r"guideline daily amount.*$", " ", text)
    text = re.sub(r"recommended dietary allowance.*$", " ", text)
    return text


def safe_float(val):
    try:
        if "%" in str(val):
            return None
        val = str(val).replace("<", "").strip()
        return float(val)
    except Exception:
        return None


def extract_strict(keyword, text, unit):
    pattern0 = rf"(?:{keyword})\s*\(?{unit}\)?\s*(?P<val>[<]?[0-9]+\.?[0-9]*)"
    match0 = re.search(pattern0, text)
    if match0:
        return safe_float(match0.group("val"))

    pattern1 = rf"(?:{keyword})[^0-9]{{0,25}}(?P<val>[<]?[0-9]+\.?[0-9]*)\s*{unit}\b"
    match1 = re.search(pattern1, text)
    if match1:
        return safe_float(match1.group("val"))

    pattern2 = rf"(?:{keyword})[^0-9]{{0,25}}\(?{unit}\)?[^0-9]{{0,15}}(?P<val>[<]?[0-9]+\.?[0-9]*)"
    match2 = re.search(pattern2, text)
    if match2:
        return safe_float(match2.group("val"))

    return None


def extract_label(keyword, text):
    pattern = rf"(?:{keyword})[^0-9]{{0,25}}(?P<val>[<]?[0-9]+\.?[0-9]*)"
    match = re.search(pattern, text)
    if match:
        return safe_float(match.group("val"))
    return None


def extract_loose_all(text):
    return re.findall(r"([a-z\s]+?)\s*([<]?[0-9]+\.?[0-9]*)\s*(kcal|g|mg)", text)


def clean_value(val, key):
    if val is None:
        return None
    if key == "carbohydrate_g" and val > 150:
        return None
    if key == "protein_g" and val > 100:
        return None
    if key == "fat_g" and val > 100:
        return None
    if key == "energy_kcal" and val > 1000:
        return None
    if key == "sodium_mg" and val > 8000:
        return None
    if key == "sugar_g" and val > 150:
        return None
    return val


SCALE_KEYS = (
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "sugar_g",
    "added_sugar_g",
    "fat_g",
    "saturated_fat_g",
    "trans_fat_g",
    "fiber_g",
    "sodium_mg",
)


def parse_nutrition(text):
    if not text or str(text).strip() == "0":
        return {}

    raw_text = text
    if looks_like_ingredient_list(raw_text):
        return {
            "energy_kcal": None,
            "protein_g": None,
            "carbohydrate_g": None,
            "sugar_g": None,
            "added_sugar_g": None,
            "fat_g": None,
            "saturated_fat_g": None,
            "trans_fat_g": None,
            "fiber_g": None,
            "sodium_mg": None,
            "confidence": 0.0,
            "basis_g": None,
            "raw_text": raw_text,
        }

    basis_g = detect_basis_g(raw_text)
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
        "sodium_mg": None,
    }

    data["energy_kcal"] = extract_strict(r"energy(?!\s+from)|calories", text, "kcal")
    kj_kcal = re.search(
        r"([0-9]+\.?[0-9]*)\s*kj\s*/\s*\(?\s*([0-9]+\.?[0-9]*)\s*kcal",
        text,
    )
    if kj_kcal:
        data["energy_kcal"] = safe_float(kj_kcal.group(2))
    data["protein_g"] = extract_strict("protein", text, "g")
    data["carbohydrate_g"] = extract_strict("carbohydrate|carbs", text, "g")
    data["fat_g"] = extract_strict(r"(?:total\s+)?fat(?!\s+acid)", text, "g")

    data["added_sugar_g"] = extract_strict("added sugars?", text, "g")
    data["sugar_g"] = (
        extract_strict(r"total sugars?", text, "g")
        or extract_strict(r"of which sugars?", text, "g")
        or extract_strict(r"(?<!added )(?<!added sugars )sugars?", text, "g")
    )

    data["saturated_fat_g"] = extract_strict("saturated", text, "g")
    data["trans_fat_g"] = extract_strict("trans", text, "g")
    data["fiber_g"] = extract_strict(r"dietary fibre|dietary fiber|fibre|fiber", text, "g")

    sodium = extract_strict("sodium", text, "mg")
    salt = extract_strict("salt", text, "g")

    if sodium is not None:
        data["sodium_mg"] = sodium
    elif salt is not None:
        data["sodium_mg"] = salt * 400

    for key, keyword in [
        ("energy_kcal", r"energy(?!\s+from)"),
        ("protein_g", "protein"),
        ("carbohydrate_g", "carbohydrate"),
    ]:
        if not data[key]:
            data[key] = extract_label(keyword, text)

    if not data["energy_kcal"]:
        data["energy_kcal"] = extract_label("calories", text)

    matches = extract_loose_all(text)

    for label, value, unit in matches:
        value = safe_float(value)
        if value is None:
            continue

        label = label.strip()

        if not data["energy_kcal"] and ("energy" in label or "calorie" in label) and unit == "kcal":
            if "from fat" in label or "diet" in label:
                continue
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
        elif not data["fat_g"] and "fat" in label and "from fat" not in label:
            data["fat_g"] = value
        elif not data["fiber_g"] and ("fiber" in label or "fibre" in label):
            data["fiber_g"] = value
        elif not data["sodium_mg"] and "sodium" in label and unit == "mg":
            data["sodium_mg"] = value
        elif not data["sodium_mg"] and "salt" in label and unit == "g":
            data["sodium_mg"] = value * 400

    for k in list(data.keys()):
        data[k] = clean_value(data[k], k)

    # mg labeled as g (e.g. sodium 1.2 g) — only boost tiny values
    if data["sodium_mg"] is not None and 0 < data["sodium_mg"] < 10:
        if re.search(r"sodium[^0-9]{0,20}[0-9.]+\s*g\b", raw_text.lower()):
            data["sodium_mg"] *= 1000

    if basis_g and basis_g != 100 and 0 < basis_g <= 80:
        energy = data.get("energy_kcal")
        factor = 100.0 / basis_g
        scaled_energy = energy * factor if energy is not None else None
        # If scaling implies >900 kcal/100g, the panel was already per 100g.
        if scaled_energy is None or scaled_energy <= 900:
            for key in SCALE_KEYS:
                if data.get(key) is not None:
                    data[key] = round(data[key] * factor, 2)

    essential = ["energy_kcal", "protein_g", "carbohydrate_g", "fat_g"]
    found = sum(1 for k in essential if data.get(k) is not None)
    data["confidence"] = round(found / len(essential), 2)
    data["basis_g"] = basis_g
    data["raw_text"] = raw_text

    return data


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

            parsed = parse_nutrition(product.get("nutrition", ""))
            product["parsed_nutrition"] = parsed
            if parsed.get("confidence", 0) < 0.5 and parsed:
                low_conf += 1
            outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
            count += 1

    print("\nPatched parser complete")
    print("Total:", count)
    print("Low confidence:", low_conf)
