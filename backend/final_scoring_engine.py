import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"

with (KNOWLEDGE_DIR / "additives.json").open(encoding="utf-8") as additives_file:
    ADDITIVES_DB = json.load(additives_file)
with (KNOWLEDGE_DIR / "meta_data.json").open(encoding="utf-8") as meta_file:
    META = json.load(meta_file)

ADDITIVES_DB = {k.lower(): v for k, v in ADDITIVES_DB.items()}


# ===== SAFE =====
def safe(v):
    return v if v is not None else 0


# ===== COMPRESSION =====
def compress_score(penalty):
    score = 100 * (1 / (1 + penalty / 50))
    return max(0, min(100, round(score, 2)))


# ===== 🔥 HUMANIZER (NEW) =====
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
        "Contains caffeine": "⚠️ Contains caffeine"
    }

    # dynamic cases
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
    }

    if "High-risk additive" in reason:
        return "Harmful additive detected"

    if "Moderate additive" in reason:
        return "Artificial additive present"

    if "Unknown additive" in reason:
        return "Unknown additive present"

    return mapping.get(reason, reason)


# ===== 🔥 FLATTEN ADDITIVES =====
def flatten_additives(additives):

    if isinstance(additives, dict):
        flat = []
        flat.extend(additives.get("primary", []))
        flat.extend(additives.get("secondary", []))
        flat.extend(additives.get("generic", []))
        return flat

    return additives or []


# ===== ADDITIVE SCORE =====
def additive_score(additives):

    score = 0
    explanations = []

    additives = flatten_additives(additives)

    for add in additives:

        if isinstance(add, str):
            code = add.lower()
            risk = "unknown"
            name = code
        else:
            code = add.get("code", "").lower()
            risk = add.get("risk", "unknown")
            name = add.get("name", code)

        if risk == "high":
            score -= 8
            explanations.append("High-risk additive")

        elif risk in ["medium", "moderate"]:
            score -= 4
            explanations.append("Moderate additive")

        elif risk == "low":
            score -= 1

        elif code in ADDITIVES_DB:
            db_risk = ADDITIVES_DB[code].get("risk", "unknown")

            if db_risk == "high":
                score -= 8
                explanations.append("High-risk additive")

            elif db_risk in ["medium", "moderate"]:
                score -= 4
                explanations.append("Moderate additive")

        else:
            score -= 2
            explanations.append("Unknown additive")

    return score, explanations


# ===== NUTRIENT SCORE =====
def nutrient_score(n):

    score = 0
    explanations = []

    sugar = safe(n.get("sugar_g"))
    added_sugar = safe(n.get("added_sugar_g"))
    sodium = safe(n.get("sodium_mg"))
    sat_fat = safe(n.get("saturated_fat_g"))
    trans_fat = safe(n.get("trans_fat_g"))
    fiber = safe(n.get("fiber_g"))
    protein = safe(n.get("protein_g"))
    energy = safe(n.get("energy_kcal"))
    carbs = safe(n.get("carbohydrate_g"))

    if energy > 0:
        ratio = (sugar * 4) / energy
        if ratio > 0.6:
            score -= 40
            explanations.append("Very high sugar density")
        elif ratio > 0.4:
            score -= 25
            explanations.append("High sugar density")

    if sodium > 1000:
        score -= 40
        explanations.append("Extremely high sodium")
    elif sodium > 500:
        score -= 20
        explanations.append("High sodium")

    if added_sugar > 20:
        score -= 40
        explanations.append("Very high added sugar")
    elif added_sugar > 10:
        score -= 20
        explanations.append("High added sugar")

    if carbs > 60:
        score -= 15
        explanations.append("High refined carbohydrates")

    if sat_fat > 10:
        score -= 25
        explanations.append("High saturated fat")

    if trans_fat > 0:
        score -= 20
        explanations.append("Contains trans fat")

    if fiber > 5:
        score += 5
        explanations.append("Good fiber")

    if protein > 10:
        score += 3
        explanations.append("Good protein")

    return score, explanations


# ===== SIGNAL SCORE =====
def signal_score(a, n):

    score = 0
    explanations = []

    raw = str(n.get("raw_text", "")).lower()
    sugar = safe(n.get("sugar_g"))
    energy = safe(n.get("energy_kcal"))

    if not n or n.get("confidence", 0) < 0.3:
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

    if energy < 100 and sugar >= 10:
        score -= 30
        explanations.append("Liquid sugar product")

    if "caffeine" in raw:
        score -= 25
        explanations.append("Contains caffeine")

    return score, explanations


# ===== FINAL SCORE =====
def final_score(product_or_n, a=None):

    if a is not None:
        n = product_or_n
    else:
        n = product_or_n.get("parsed_nutrition", {})
        a = product_or_n.get("ingredient_analysis", {})

    total_penalty = 0
    all_explanations = []

    s, exp = nutrient_score(n)
    total_penalty += max(0, -s)
    all_explanations.extend(exp)

    s, exp = additive_score(a.get("additives", {}))
    total_penalty += max(0, -s)
    all_explanations.extend(exp)

    s, exp = signal_score(a, n)
    total_penalty += max(0, -s)
    all_explanations.extend(exp)

    score = compress_score(total_penalty)

    # 🔥 CLEAN + HUMANIZE
    final_reasons = list(set(humanize_reason(r) for r in all_explanations))

    return score, final_reasons


# ===== VERDICT =====
def get_verdict(score):
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Moderate"
    else:
        return "Unhealthy"
