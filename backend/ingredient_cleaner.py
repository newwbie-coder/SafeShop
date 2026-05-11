import re


# ===== REMOVE PHRASES =====
REMOVE_PHRASES = [
    "contains",
    "may contain",
    "allergen",
    "information",
    "declaration",
    "permitted",
    "added",
]


# ===== NORMALIZE COMMON NOISE =====
REPLACEMENTS = {
    "flavours flavouring substances": "flavour",
    "flavouring substances": "flavour",
    "artificial flavours": "flavour",
    "nature identical flavour": "flavour",
    "natural flavour": "flavour",

    "vegetable oils": "vegetable oil",
    "hydrogenated vegetable oil": "hydrogenated oil",
}


# ===== STRONG INGREDIENT ANCHORS =====
ANCHORS = [
    "sugar", "salt", "oil", "flour", "milk", "butter",
    "cocoa", "starch", "glucose", "syrup", "cream",
    "chocolate", "water", "protein", "fiber", "malt"
]


# ===== HARD KEEP (never split) =====
KEEP_PHRASES = [
    "milk chocolate",
    "cocoa butter",
    "wheat flour",
    "refined wheat flour",
    "whole wheat flour",
    "palm oil",
    "vegetable oil",
    "glucose syrup",
    "milk solids",
]


# ===== CLEAN TEXT =====
def basic_clean(text):

    text = text.lower()

    for p in REMOVE_PHRASES:
        text = text.replace(p, " ")

    for k, v in REPLACEMENTS.items():
        text = text.replace(k, v)

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ===== SPLIT SMART =====
def smart_split(token):

    words = token.split()

    if len(words) <= 2:
        return [token]

    # preserve important phrases
    for phrase in KEEP_PHRASES:
        if phrase in token:
            return [phrase]

    parts = []
    current = []

    for w in words:

        if w in ANCHORS:
            if current:
                parts.append(" ".join(current))
                current = []

            parts.append(w)
        else:
            current.append(w)

    if current:
        parts.append(" ".join(current))

    return parts


# ===== CLEAN SINGLE TOKEN =====
def clean_token(token):

    token = basic_clean(token)

    token = re.sub(r"\b\d+\b", "", token).strip()

    if len(token) < 3:
        return None

    return token


# ===== MAIN CLEANER =====
def clean_ingredients(ingredients):

    final = []

    for ing in ingredients:

        if not ing:
            continue

        ing = clean_token(ing)

        if not ing:
            continue

        split_items = smart_split(ing)

        for item in split_items:

            item = item.strip()

            if len(item) < 3:
                continue

            final.append(item)

    # ===== FINAL FILTER =====
    cleaned = []

    for item in final:

        # remove garbage combos
        if "contains" in item:
            continue

        if item.startswith("and "):
            continue

        cleaned.append(item)

    return list(dict.fromkeys(cleaned))