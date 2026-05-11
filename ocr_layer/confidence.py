def compute_confidence(raw_text, ingredients, nutrition, ocr_conf):

    score = 0

    # ===== 1. TEXT QUALITY =====
    if len(raw_text) > 50:
        score += 0.25
    elif len(raw_text) > 20:
        score += 0.15

    # ===== 2. INGREDIENTS (PRIMARY SIGNAL) =====
    if ingredients:
        score += 0.4   # higher weight (very important)

    # ===== 3. NUTRITION (SECONDARY SIGNAL) =====
    if nutrition:
        score += 0.25
    else:
        # don't penalize too much if missing
        score += 0.05

    # ===== 4. OCR CONFIDENCE =====
    score += (ocr_conf * 0.1)

    # ===== 5. PENALTY FOR VERY LOW CONTENT =====
    if len(raw_text.strip()) < 10:
        score *= 0.5

    return round(min(score, 1.0), 2)