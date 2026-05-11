import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
UNKNOWN_ADDITIVES_PATH = KNOWLEDGE_DIR / "unknown_additives.txt"

with (KNOWLEDGE_DIR / "additives.json").open(encoding="utf-8") as f:
    ADDITIVES_DB = json.load(f)

ADDITIVES_DB = {k.lower(): v for k, v in ADDITIVES_DB.items()}


# ===== GENERIC ADDITIVES =====
GENERIC_ADDITIVES = [
    "flavour",
    "flavour enhancer",
    "generic_emulsifier",
    "generic_stabilizer",
    "acidity_regulator",
    "raising_agent",
    "thickener",
    "colour",
    "color",
    "generic_preservative",
    "antioxidant",
    "anti_caking"
]


# ===== SIGNAL LISTS =====
MSG_CODES = ["ins621", "ins627", "ins631", "ins635"]

PROCESSED_OILS = [
    "palm oil",
    "hydrogenated oil",
    "hydrogenated",
    "shortening"
]

SWEETENERS = [
    "aspartame",
    "sucralose",
    "acesulfame",
    "saccharin",
    "maltitol"
]

ULTRA_PROCESSED_SIGNALS = [
    "flavour",
    "flavouring",
    "modified starch",
    "maltodextrin",
    "glucose syrup",
    "compound coating"
]

ARTIFICIAL_COLORS = [
    "e102", "e110", "e122", "e124", "e129",
    "ins102", "ins110", "ins122", "ins124", "ins129"
]


# ===== HELPERS =====
def normalize_code(code: str):
    code = code.lower().replace(" ", "")

    if code.isdigit():
        return f"ins{code}"

    if not code.startswith("ins") and not code.startswith("e"):
        return f"ins{code}"

    return code


def extract_additives(text):
    pattern = r"(ins\s?\d{3,4}[a-z]?|e\s?\d{3,4}[a-z]?|\b\d{3,4}\b)"
    matches = re.findall(pattern, text.lower())

    return list(set(normalize_code(m) for m in matches))


def add_unique(lst, item):
    if not any(a["code"] == item["code"] for a in lst):
        lst.append(item)


# ===== 🔥 STRONG RESOLVER =====
def resolve_additive(code):
    code = normalize_code(code)
    visited = set()

    while code and code not in visited:
        visited.add(code)

        info = ADDITIVES_DB.get(code)

        if not info:
            alt = code.replace("ins", "e") if code.startswith("ins") else code.replace("e", "ins")
            info = ADDITIVES_DB.get(alt)

        if not info:
            return None

        if "ref" in info:
            code = info["ref"].lower()
            continue

        return {
            "code": code,
            "name": info.get("name", "Unknown additive"),
            "risk": info.get("risk", "unknown"),
            "category": info.get("category", "unknown")
        }

    return None


# ===== 🔥 UNKNOWN LOGGER =====
def log_unknown_additive(code):
    try:
        UNKNOWN_ADDITIVES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with UNKNOWN_ADDITIVES_PATH.open("a", encoding="utf-8") as f:
            f.write(code + "\n")
    except Exception:
        pass


# ===== MAIN ANALYZER =====
def analyze_ingredients(ingredients):

    result = {
        "additives": {
            "primary": [],
            "secondary": [],
            "generic": []
        },
        "msg": False,
        "sweeteners": [],
        "processed_oils": [],
        "ultra_processed": False,
        "artificial_colors": [],
        "unknown_additives": []   # 🔥 NEW
    }

    if not ingredients:
        return result

    text = " ".join(ingredients) if isinstance(ingredients, list) else ingredients

    lower = text.lower()
    normalized = lower.replace(" ", "")

    additive_details = []

    # ===== 1. CODE DETECTION =====
    for code in extract_additives(text):

        resolved = resolve_additive(code)

        if resolved:
            add_unique(additive_details, resolved)
        else:
            clean_code = normalize_code(code)

            # 🔥 log unknown
            result["unknown_additives"].append(clean_code)
            log_unknown_additive(clean_code)

            add_unique(additive_details, {
                "code": clean_code,
                "name": f"Unknown additive: {clean_code.upper()}",
                "risk": "unknown",
                "category": "unknown"
            })

    # ===== 2. NAME DETECTION =====
    for key, info in ADDITIVES_DB.items():

        if key.startswith("ins") or key.startswith("e"):
            continue

        if key in lower:
            add_unique(additive_details, {
                "code": key,
                "name": info.get("name", key),
                "risk": info.get("risk", "unknown"),
                "category": info.get("category", "unknown")
            })

    # ===== 3. GENERIC DETECTION =====
    for word in GENERIC_ADDITIVES:
        if word in lower:
            add_unique(additive_details, {
                "code": word,
                "name": word,
                "risk": "moderate",
                "category": "generic_additive"
            })

    # ===== 4. CLASSIFICATION =====
    primary, secondary, generic = [], [], []

    for a in additive_details:
        code = a.get("code", "")
        risk = a.get("risk", "unknown")

        if code.startswith("ins") or code.startswith("e"):
            add_unique(primary, a)

        elif risk != "unknown" and a.get("category") != "generic_additive":
            add_unique(secondary, a)

        else:
            add_unique(generic, a)

    result["additives"] = {
        "primary": primary,
        "secondary": secondary,
        "generic": generic
    }

    # ===== FLAGS =====
    for code in MSG_CODES:
        if code in normalized:
            result["msg"] = True

    for s in SWEETENERS:
        if s in lower:
            result["sweeteners"].append(s)

    for oil in PROCESSED_OILS:
        if oil in lower:
            result["processed_oils"].append(oil)

    for signal in ULTRA_PROCESSED_SIGNALS:
        if signal in lower:
            result["ultra_processed"] = True

    for color in ARTIFICIAL_COLORS:
        if color in normalized:
            result["artificial_colors"].append(color)

    return result