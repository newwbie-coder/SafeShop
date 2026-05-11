import re

INGREDIENTS_KEYWORDS = [
    "ingredients", "ingredient list", "contains"
]

NUTRITION_KEYWORDS = [
    "nutrition", "nutritional", "energy", "calories"
]


def extract_ingredients(text):
    for key in INGREDIENTS_KEYWORDS:
        pattern = rf"{key}[:\-\s]*(.*?)(nutrition|energy|$)"
        match = re.search(pattern, text)

        if match:
            return match.group(1).strip()

    return ""


def extract_nutrition(text):
    for key in NUTRITION_KEYWORDS:
        pattern = rf"({key}.*)"
        match = re.search(pattern, text)

        if match:
            return match.group(1).strip()

    return ""