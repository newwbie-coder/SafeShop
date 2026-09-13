import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"

with (KNOWLEDGE_DIR / "additives.json").open(encoding="utf-8") as additives_file:
    ADDITIVES_DB = json.load(additives_file)
with (KNOWLEDGE_DIR / "meta_data.json").open(encoding="utf-8") as meta_file:
    META = json.load(meta_file)

ADDITIVES_DB = {k.lower(): v for k, v in ADDITIVES_DB.items()}

REFINED_CARB_TOKENS = (
    "refined wheat flour",
    "maida",
    "corn grit",
    "liquid glucose",
    "maltodextrin",
    "glucose syrup",
)


def present(v):
    return v is not None


def safe(v):
    return v if v is not None else 0


def compress_score(penalty):
    score = 100 * (1 / (1 + penalty / 50))
    return max(0, min(100, round(score, 2)))


def humanize(reason):
    mapping = {
        "Very high sugar density": "🚨 Extremely high sugar (very unhealthy)",
        "High sugar density": "⚠️ High sugar content",
        "Extremely high sodium": "🚨 Extremely high salt (BP risk)",
        "High sodium": "⚠️ High salt (can increase BP)",
        "Very high added sugar": "🚨 Very high added sugar",
        "High added sugar": "⚠️ High added sugar",
        "High refined carbohydrates": "⚠️ Refined carbs (low nutrition)",
        "High saturated fat": "⚠️ High saturated fat",
        "Contains trans fat": "🚨 Contains trans fat (heart risk)",
        "Good fiber": "✅ Good fiber content",
        "Good protein": "✅ Good protein content",
        "Insufficient nutrition data": "⚠️ Nutrition data incomplete",
        "Contains MSG": "⚠️ Contains MSG (flavour enhancer)",
        "Ultra-processed product": "⚠️ Highly processed product",
        "Contains processed oils": "⚠️ Refined/processed oils used",
        "Contains artificial sweeteners": "⚠️ Artificial sweeteners present",
        "Contains artificial colors": "⚠️ Artificial colors present",
        "Liquid sugar product": "🚨 Liquid sugar (very unhealthy)",
        "Contains caffeine": "⚠️ Contains caffeine",
        "Very high sugar per 100g": "🚨 Extremely high sugar (very unhealthy)",
    }
    if "High-risk additive" in reason:
        return "🚨 Harmful additive detected"
    if "Moderate additive" in reason:
        return "⚠️ Artificial additive present"
    if "Unknown additive" in reason:
        return "⚠️ Unknown additive present"
    return mapping.get(reason, reason)


def humanize_reason(reason):
    mapping = {
        "Very high sugar density": "Extremely high sugar (very unhealthy)",
        "High sugar density": "High sugar content",
        "Extremely high sodium": "Extremely high salt (BP risk)",
        "High sodium": "High salt (can increase BP)",
        "Very high added sugar": "Very high added sugar",
        "High added sugar": "High added sugar",
        "High refined carbohydrates": "Refined carbs (low nutrition)",
        "High saturated fat": "High saturated fat",
        "Contains trans fat": "Contains trans fat (heart risk)",
        "Good fiber": "Good fiber content",
        "Good protein": "Good protein content",
        "Insufficient nutrition data": "Nutrition data incomplete",
        "Contains MSG": "Contains MSG (flavour enhancer)",
        "Ultra-processed product": "Highly processed product",
        "Contains processed oils": "Refined/processed oils used",
        "Contains artificial sweeteners": "Artificial sweeteners present",
        "Contains artificial colors": "Artificial colors present",
        "Liquid sugar product": "Liquid sugar (very unhealthy)",
        "Contains caffeine": "Contains caffeine",
        "Very high sugar per 100g": "Extremely high sugar (very unhealthy)",
    }
    if "High-risk additive" in reason:
        return "Harmful additive detected"
    if "Moderate additive" in reason:
        return "Artificial additive present"
    if "Unknown additive" in reason:
        return "Unknown additive present"
    return mapping.get(reason, reason)


def flatten_additives(additives):
    if isinstance(additives, dict):
        flat = []
        flat.extend(additives.get("primary", []))
        flat.extend(additives.get("secondary", []))
        flat.extend(additives.get("generic", []))
        return flat
    return additives or []


def additive_score(additives):
    score = 0
    explanations = []
    additives = flatten_additives(additives)

    generic_hits = 0
    coded_hits = 0

    for add in additives:
        if isinstance(add, str):
            code = add.lower()
            risk = "unknown"
        else:
            code = (add.get("code") or "").lower()
            risk = add.get("risk", "unknown")

        is_generic = add.get("category") == "generic_additive" if isinstance(add, dict) else False
        is_coded = code.startswith("ins") or code.startswith("e")

        if risk == "unknown" and code in ADDITIVES_DB:
            risk = ADDITIVES_DB[code].get("risk", "unknown")

        if is_generic:
            if coded_hits > 0:
                continue
            if generic_hits >= 3:
                continue
            generic_hits += 1
            score -= 4
            explanations.append("Moderate additive")
            continue

        if risk == "high":
            score -= 8
            explanations.append("High-risk additive")
            if is_coded:
                coded_hits += 1
        elif risk in ["medium", "moderate"]:
            score -= 4
            explanations.append("Moderate additive")
            if is_coded:
                coded_hits += 1
        elif risk == "low":
            score -= 1
            if is_coded:
                coded_hits += 1
        elif is_coded:
            score -= 2
            explanations.append("Unknown additive")
            coded_hits += 1
        else:
            if generic_hits >= 3:
                continue
            generic_hits += 1
            score -= 2
            explanations.append("Unknown additive")

    return score, explanations


def nutrient_score(n, tokens=None):
    score = 0
    explanations = []
    tokens = tokens or []
    token_blob = " ".join(str(t).lower() for t in tokens)

    sugar = n.get("sugar_g")
    added_sugar = n.get("added_sugar_g")
    sodium = n.get("sodium_mg")
    sat_fat = n.get("saturated_fat_g")
    trans_fat = n.get("trans_fat_g")
    fiber = n.get("fiber_g")
    protein = n.get("protein_g")
    energy = n.get("energy_kcal")
    carbs = n.get("carbohydrate_g")

    if present(energy) and energy > 0 and present(sugar):
        ratio = (sugar * 4) / energy
        if ratio > 0.6:
            score -= 40
            explanations.append("Very high sugar density")
        elif ratio > 0.4:
            score -= 25
            explanations.append("High sugar density")

    if present(sugar) and sugar >= 50:
        score -= 25
        explanations.append("Very high sugar per 100g")

    if present(sodium):
        if sodium > 1000:
            score -= 40
            explanations.append("Extremely high sodium")
        elif sodium > 500:
            score -= 20
            explanations.append("High sodium")

    if present(added_sugar):
        if added_sugar > 20:
            score -= 40
            explanations.append("Very high added sugar")
        elif added_sugar > 10:
            score -= 20
            explanations.append("High added sugar")

    low_fiber = (not present(fiber)) or fiber < 3
    refined = any(t in token_blob for t in REFINED_CARB_TOKENS)
    if present(carbs) and carbs > 60 and low_fiber:
        score -= 15
        explanations.append("High refined carbohydrates")
    elif present(carbs) and carbs > 60 and refined:
        score -= 15
        explanations.append("High refined carbohydrates")

    if present(sat_fat) and sat_fat > 10:
        score -= 25
        explanations.append("High saturated fat")

    if present(trans_fat) and trans_fat > 0.2:
        score -= 20
        explanations.append("Contains trans fat")

    if present(fiber) and fiber > 5:
        score += 5
        explanations.append("Good fiber")

    if present(protein) and protein > 10:
        score += 3
        explanations.append("Good protein")

    return score, explanations


def signal_score(a, n):
    score = 0
    explanations = []

    raw = str(n.get("raw_text", "")).lower()
    sugar = n.get("sugar_g")
    energy = n.get("energy_kcal")
    confidence = n.get("confidence", 0) if n else 0

    if not n or confidence < 0.3:
        score -= 30
        explanations.append("Insufficient nutrition data")

    if a.get("msg"):
        score -= 15
        explanations.append("Contains MSG")

    if a.get("ultra_processed"):
        score -= 30
        explanations.append("Ultra-processed product")

    if a.get("processed_oils"):
        score -= 5
        explanations.append("Contains processed oils")

    if a.get("sweeteners"):
        score -= 5
        explanations.append("Contains artificial sweeteners")

    if a.get("artificial_colors"):
        score -= 5
        explanations.append("Contains artificial colors")

    if present(energy) and present(sugar) and energy < 100 and sugar >= 10:
        score -= 30
        explanations.append("Liquid sugar product")

    if "caffeine" in raw or a.get("caffeine"):
        score -= 15
        explanations.append("Contains caffeine")

    return score, explanations


def _has_real_ingredients(product, a):
    tokens = product.get("tokens") or product.get("ingredients") or []
    if isinstance(tokens, str):
        return bool(tokens.strip())
    if tokens:
        return True
    additives = flatten_additives((a or {}).get("additives", {}))
    return bool(additives)


def final_score(product_or_n, a=None):
    if a is not None:
        n = product_or_n
        product = {}
        tokens = []
    else:
        n = product_or_n.get("parsed_nutrition", {}) or {}
        a = product_or_n.get("ingredient_analysis", {}) or {}
        product = product_or_n
        tokens = product_or_n.get("tokens") or product_or_n.get("ingredients") or []

    if isinstance(tokens, str):
        tokens = [tokens]

    total_penalty = 0
    all_explanations = []

    s, exp = nutrient_score(n, tokens)
    total_penalty -= s
    all_explanations.extend(exp)

    s, exp = additive_score(a.get("additives", {}))
    total_penalty -= s
    all_explanations.extend(exp)

    s, exp = signal_score(a, n)
    total_penalty -= s
    all_explanations.extend(exp)

    total_penalty = max(0, total_penalty)
    score = compress_score(total_penalty)

    thin_data = (not n) or n.get("confidence", 0) < 0.5 or not present(n.get("energy_kcal"))
    no_ingredients = not _has_real_ingredients(product, a)
    if total_penalty == 0 and (thin_data or no_ingredients):
        score = 58.0
        if "Insufficient nutrition data" not in all_explanations:
            all_explanations.append("Insufficient nutrition data")

    sugar = n.get("sugar_g")
    protein = n.get("protein_g")
    fiber = n.get("fiber_g")
    whole = (protein or 0) >= 10 or (fiber or 0) >= 5
    sugary = (sugar or 0) >= 15 or (n.get("added_sugar_g") or 0) >= 10
    if no_ingredients and score >= 70 and (sugary or not whole):
        score = min(score, 64.0)
        if "Insufficient nutrition data" not in all_explanations:
            all_explanations.append("Insufficient nutrition data")

    final_reasons = list(dict.fromkeys(humanize_reason(r) for r in all_explanations))
    return score, final_reasons


def get_verdict(score):
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Moderate"
    else:
        return "Unhealthy"
