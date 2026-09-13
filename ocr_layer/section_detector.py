import re

INGREDIENTS_KEYWORDS = [
    "ingredients",
    "ingredient list",
    "composition",
]

NUTRITION_KEYWORDS = [
    "nutritional information",
    "nutrition information",
    "nutrition facts",
    "nutrition",
    "nutritional",
    "energy",
    "calories",
]


def extract_ingredients(text):
    if not text:
        return ""
    lowered = text.lower()
    for key in INGREDIENTS_KEYWORDS:
        pattern = rf"{key}[:\-\s]*(.*?)(?=nutritional information|nutrition information|nutrition facts|nutrition\b|energy\b|kcal|$)"
        match = re.search(pattern, lowered, flags=re.S)
        if match:
            blob = match.group(1).strip(" :-")
            if len(blob) > 8:
                return blob
    return ""


def extract_nutrition(text):
    if not text:
        return ""
    lowered = text.lower()
    for key in NUTRITION_KEYWORDS:
        pattern = rf"({key}.*)"
        match = re.search(pattern, lowered, flags=re.S)
        if match:
            blob = match.group(1).strip()
            if len(blob) > 8:
                return blob
    return ""


def looks_like_nutrition_blob(text):
    t = (text or "").lower()
    return bool(re.search(r"\b(kcal|energy|protein|carbohydrate|sodium)\b", t) and re.search(r"\d", t))


def looks_like_ingredient_blob(text):
    t = (text or "").lower()
    if looks_like_nutrition_blob(t):
        return False
    food = bool(re.search(
        r"\b(wheat|sugar|oil|salt|milk|flour|cocoa|oats|rice|maida|palm|soy|corn)\b",
        t,
    ))
    listed = t.count(",") >= 2 and len(t) > 40
    return food or listed


def _split_around(text, blob):
    raw = text or ""
    needle = (blob or "")[:24].lower()
    if not needle:
        return raw.strip(), ""
    idx = raw.lower().find(needle)
    if idx < 0:
        return raw.strip(), ""
    return raw[:idx].strip(" :-"), raw[idx:].strip()


def split_label_text(text):
    """Split OCR/raw label text into ingredients + nutrition with safe fallbacks."""
    ingredients = extract_ingredients(text)
    nutrition = extract_nutrition(text)

    if ingredients and not nutrition:
        _, rest = _split_around(text, ingredients[-24:] if ingredients else "")
        if looks_like_nutrition_blob(rest):
            nutrition = rest
    if nutrition and not ingredients:
        prefix, _ = _split_around(text, nutrition)
        if (
            looks_like_ingredient_blob(prefix)
            and ("," in prefix or len(prefix) > 28)
            and not re.match(r"contains\b", prefix.lower())
        ):
            ingredients = prefix

    if not ingredients and not nutrition:
        if looks_like_nutrition_blob(text):
            nutrition = (text or "").strip()
        elif looks_like_ingredient_blob(text):
            ingredients = (text or "").strip()
        elif text and re.search(r"\d", text):
            nutrition = text.strip()
        elif text:
            ingredients = text.strip()

    return ingredients, nutrition
