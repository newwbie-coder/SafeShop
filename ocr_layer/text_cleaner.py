import re

def clean_text(text):
    if not text:
        return ""

    text = text.lower()

    # remove weird OCR artifacts
    text = re.sub(r"[^a-z0-9%.,:\-\s()]", " ", text)

    # normalize spacing
    text = re.sub(r"\s+", " ", text)

    # fix common OCR mistakes
    text = text.replace("ingre dients", "ingredients")
    text = text.replace("nutri tion", "nutrition")

    return text.strip()