import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "sample"
INPUT = DATA_DIR / "sample_products.jsonl"
OUTPUT = DATA_DIR / "sample_products_normalized.jsonl"


# ===== NORMALIZATION MAP =====
NORMALIZATION_MAP = {
    "maida": "refined wheat flour",
    "atta": "whole wheat flour",

    "lodised salt": "salt",
    "lodized salt": "salt",
    "iodised salt": "salt",

    "palmolein": "palm oil",
    "hydrogenated vegetable fats": "hydrogenated oil",
    "hydrogenated oils": "hydrogenated oil",

    # oils fix 🔥
    "soyabean oil": "refined vegetable oil",
    "sunflower oil": "refined vegetable oil",
    "vegetable oils": "refined vegetable oil",
    "edible vegetable oil": "refined vegetable oil",

    "monosodium glutamate": "ins621",
    "msg": "ins621",

    "sweetner": "sweetener",
}


# ===== GENERIC MAP =====
GENERIC_MAP = {
    "emulsifier": "generic_emulsifier",
    "stabilizer": "generic_stabilizer",
    "stabilisers": "generic_stabilizer",

    "raising agent": "raising_agent",
    "raising agents": "raising_agent",

    "acidity regulator": "acidity_regulator",
    "acid": "acidity_regulator",
    "acidulant": "acidity_regulator",

    "preservative": "generic_preservative",
    "preservatives": "generic_preservative",

    "anticaking agent": "anti_caking",

    "colour": "colour",
    "colours": "colour",

    "flavour": "flavour",
    "flavours": "flavour",

    "antioxidant": "antioxidant",
    "antioxidants": "antioxidant",
}


# ===== REMOVE JUNK PHRASES =====
REMOVE_PHRASES = [
    "contains",
    "may contain",
    "allergen information",
    "allergen declaration",
    "permitted",
]


# ===== SPELL FIX =====
SPELL_FIX = {
    "maltodextrine": "maltodextrin",
}


# ===== CLEAN TEXT =====
def clean_text(text):

    text = text.lower()

    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"\{.*?\}", " ", text)
    text = re.sub(r"\[.*?\]", " ", text)

    text = re.sub(r"ingredients?:", " ", text)

    for phrase in REMOVE_PHRASES:
        text = text.replace(phrase, " ")

    text = re.sub(r"[^a-z0-9,.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ===== SMART SPLIT =====
def smart_split(text):

    parts = re.split(r",|\.", text)

    final = []

    for p in parts:
        sub = re.split(
            r"\band\b|with|mix|blend|powder|extract|sauce|cream|coating|filling",
            p
        )
        final.extend(sub)

    return [x.strip() for x in final if x.strip()]


# ===== FIX MERGED WORDS =====
def fix_merged_words(token):

    fixes = {
        "pepperarlic": "pepper garlic",
        "fenugreekinger": "fenugreek ginger",
        "lodised": "iodised",
    }

    for k, v in fixes.items():
        token = token.replace(k, v)

    return token


# ===== VALID TOKEN FILTER =====
def is_valid_token(token):

    if len(token) < 3:
        return False

    # remove long garbage phrases
    if len(token.split()) > 4:
        return False

    # remove mixed junk phrases
    bad_words = ["noodles", "condiments", "soup", "mix", "blend"]
    if sum(1 for w in bad_words if w in token) >= 2:
        return False

    return True


# ===== NORMALIZE TOKEN =====
def normalize_token(token):

    token = fix_merged_words(token)

    # remove numbers
    token = re.sub(r"\b\d+\b", "", token).strip()

    if not is_valid_token(token):
        return None

    # ===== INS DETECTION =====
    match = re.search(r"(e|ins)\s?(\d{3,4}[a-z]?)", token)
    if match:
        return f"ins{match.group(2)}"

    if re.fullmatch(r"\d{3,4}", token):
        return f"ins{token}"

    # ===== SPELL FIX =====
    for k, v in SPELL_FIX.items():
        if k in token:
            return v

    # ===== MAPS =====
    for k, v in NORMALIZATION_MAP.items():
        if k in token:
            return v

    for k, v in GENERIC_MAP.items():
        if k in token:
            return v

    # ===== REMOVE USELESS TOKENS =====
    if token in ["oil", "water", "food", "product", "natural", "cereal", "mineral", "centre"]:
        return None

    return token


# ===== FINAL NORMALIZER =====
def normalize_ingredients(text):

    if not text:
        return []

    text = clean_text(text)

    tokens = smart_split(text)

    result = []

    for t in tokens:
        norm = normalize_token(t)
        if not norm:
            continue
        result.append(norm)

    return list(dict.fromkeys(result))  # remove duplicates, keep order


# ===== MAIN =====
if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open(encoding="utf-8") as infile, \
         OUTPUT.open("w", encoding="utf-8") as outfile:

        count = 0

        for line in infile:
            try:
                product = json.loads(line)
            except Exception:
                continue

            ing = product.get("ingredients", "")
            product["ingredients"] = normalize_ingredients(ing)

            outfile.write(json.dumps(product, ensure_ascii=False) + "\n")
            count += 1

    print("Done:", count)