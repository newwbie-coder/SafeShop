import re

def clean_text(text):
    if not text:
        return ""

    text = text.lower()

    # remove weird OCR artifacts
    text = re.sub(r"[^a-z0-9%.,:\-\s()]", " ", text)

    # normalize spacing
    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"\b[il1]ngredients\b", "ingredients", text)
    for broken, fixed in (
        ("ingre dients", "ingredients"),
        ("nutri tion", "nutrition"),
        ("nutritlon", "nutrition"),
        ("nutrlton", "nutrition"),
        ("proteln", "protein"),
        ("sodlum", "sodium"),
        ("carbohydrete", "carbohydrate"),
        ("carbohvdrate", "carbohydrate"),
        ("transfat", "trans fat"),
    ):
        text = text.replace(broken, fixed)

    return text.strip()