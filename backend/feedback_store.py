"""Append-only user feedback. Classified for later rule/ML updates — never auto-applied."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FEEDBACK_PATH = ROOT_DIR / "data" / "feedback.jsonl"


def contemplate(comment: str, score_shown: float | None = None) -> dict:
    """Rule-based reading of feedback. No model call, no score change."""
    text = (comment or "").lower()
    issue = "other"
    suggested = "Review on next engine pass; do not auto-apply."
    confidence = 0.35

    if re.search(r"too (high|healthy|lenient|generous)|should be lower", text):
        issue = "score_too_lenient"
        suggested = "Check missing additives, sugar density, or serving-size scaling."
        confidence = 0.55
    elif re.search(r"too (low|harsh|strict|unhealthy)|should be higher", text):
        issue = "score_too_strict"
        suggested = "Check false UPF/generic-additive hits or over-counted INS codes."
        confidence = 0.55
    elif re.search(r"wrong ingredient|ocr|misread|not this product", text):
        issue = "extraction_error"
        suggested = "Prefer catalog lookup; do not trust this OCR blob for training."
        confidence = 0.6
    elif re.search(r"missing|incomplete|no nutrition|no ingredient", text):
        issue = "missing_label"
        suggested = "Try catalog + OCR fallback; do not treat empty labels as Healthy."
        confidence = 0.5

    if score_shown is not None and score_shown >= 70 and "unhealthy" in text:
        issue = "score_too_lenient"
        confidence = max(confidence, 0.5)

    return {
        "issue": issue,
        "suggested_rule": suggested,
        "confidence": confidence,
    }


def record_feedback(
    *,
    comment: str,
    name: str | None = None,
    brand: str | None = None,
    product_id: str | None = None,
    score_shown: float | None = None,
    verdict_shown: str | None = None,
) -> dict:
    summary = contemplate(comment, score_shown)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "product_id": product_id or "",
        "name": name or "",
        "brand": brand or "",
        "score_shown": score_shown,
        "verdict_shown": verdict_shown or "",
        "comment": comment,
        **summary,
    }
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
