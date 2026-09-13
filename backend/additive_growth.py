"""Grow additives.json from the unknown-code queue.

Locked policy:
- /analyze only logs unknown INS/E codes. It never calls an LLM and never
  writes additives.json.
- Promote into knowledge on a manual update (`--force`) OR when 100+ unique
  unknown codes are waiting (`GROW_THRESHOLD`).
- Known Codex codes get a name + severity from additive_codex. Parser junk is
  rejected. Leftovers stay queued for a later LLM pass.
- `--apply` is the only way into live additives.json.
"""
from __future__ import annotations

import argparse
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .additive_codex import CODEX

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
ADDITIVES_PATH = KNOWLEDGE_DIR / "additives.json"
QUEUE_PATH = KNOWLEDGE_DIR / "unknown_additives.json"
LEGACY_TXT_PATH = KNOWLEDGE_DIR / "unknown_additives.txt"
PROPOSED_PATH = KNOWLEDGE_DIR / "additives_proposed.json"

GROW_THRESHOLD = 100
_lock = threading.Lock()

_INS_RE = re.compile(r"^ins(\d{3,4})([a-z])?$")
_OK_LETTERS = set("abcdei")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _migrate_legacy_txt(queue: dict) -> dict:
    if not LEGACY_TXT_PATH.is_file():
        return queue
    try:
        lines = LEGACY_TXT_PATH.read_text(encoding="utf-8").splitlines()
    except Exception:
        return queue
    stamp = _now()
    for line in lines:
        code = line.strip().lower()
        if not code:
            continue
        row = queue.setdefault(code, {"count": 0, "first_seen": stamp, "last_seen": stamp})
        row["count"] += 1
        row["last_seen"] = stamp
    return queue


def load_queue() -> dict:
    with _lock:
        queue = _load_json(QUEUE_PATH, {})
        if not queue:
            queue = _migrate_legacy_txt({})
            if queue:
                _write_json(QUEUE_PATH, queue)
        return queue


def log_unknown_additive(code: str) -> None:
    code = (code or "").strip().lower().replace(" ", "")
    if not code:
        return
    stamp = _now()
    with _lock:
        queue = _load_json(QUEUE_PATH, {})
        if not queue:
            queue = _migrate_legacy_txt({})
        row = queue.get(code)
        if row:
            row["count"] = int(row.get("count") or 0) + 1
            row["last_seen"] = stamp
        else:
            queue[code] = {"count": 1, "first_seen": stamp, "last_seen": stamp}
        _write_json(QUEUE_PATH, queue)


def load_additives_db(path: Path | None = None) -> dict:
    data = _load_json(path or ADDITIVES_PATH, {})
    return {str(k).lower(): v for k, v in data.items()}


def pending_unknowns(queue: dict | None = None, db: dict | None = None) -> dict:
    queue = queue if queue is not None else load_queue()
    db = db if db is not None else load_additives_db()
    pending = {}
    for code, row in queue.items():
        if code in db:
            continue
        alt = code.replace("ins", "e", 1) if code.startswith("ins") else ""
        if alt and alt in db:
            continue
        pending[code] = row
    return pending


def growth_due(pending: dict | None = None, force: bool = False) -> bool:
    if force:
        return True
    pending = pending if pending is not None else pending_unknowns()
    return len(pending) >= GROW_THRESHOLD


def plausible_ins(code: str) -> bool:
    match = _INS_RE.match(code or "")
    if not match:
        return False
    digits, letter = match.group(1), match.group(2)
    if digits != str(int(digits)):
        return False
    if letter and letter not in _OK_LETTERS:
        return False
    number = int(digits)
    if 100 <= number <= 999:
        return True
    if 1100 <= number <= 1105:
        return True
    if 1200 <= number <= 1202:
        return True
    if 1400 <= number <= 1452:
        return True
    if 1505 <= number <= 1522:
        return True
    return False


def _entry_payload(code: str, info: dict) -> dict:
    number = re.sub(r"^ins", "", code)
    return {
        "name": info["name"],
        "category": info["category"],
        "risk": info["risk"],
        "e_number": f"e{number}",
    }


def classify_code(code: str, db: dict | None = None) -> dict:
    """Return a proposed additives.json fragment or a reject/pending marker."""
    db = db if db is not None else load_additives_db()
    code = (code or "").strip().lower()

    if code in CODEX:
        payload = _entry_payload(code, CODEX[code])
        alias = {"ref": code}
        e_code = payload["e_number"]
        return {
            "status": "ready",
            "entries": {code: payload, e_code: alias},
        }

    match = _INS_RE.match(code)
    if match:
        parent = f"ins{int(match.group(1))}"
        if parent in db and parent != code:
            return {
                "status": "ready",
                "entries": {code: {"ref": parent}},
            }
        if parent in CODEX and parent != code:
            return {
                "status": "ready",
                "entries": {code: {"ref": parent}},
            }

    if not plausible_ins(code):
        return {"status": "rejected", "reason": "not a plausible INS code"}

    return {"status": "pending", "reason": "needs LLM/manual review"}


def propose_growth(force: bool = False) -> dict:
    db = load_additives_db()
    pending = pending_unknowns(db=db)
    ready_gate = growth_due(pending, force=force)
    proposed = {}
    rejected = {}
    leftover = {}

    if not ready_gate:
        return {
            "due": False,
            "pending": len(pending),
            "threshold": GROW_THRESHOLD,
            "proposed": proposed,
            "rejected": rejected,
            "leftover": leftover,
        }

    for code, row in sorted(pending.items(), key=lambda item: -int(item[1].get("count") or 0)):
        result = classify_code(code, db=db)
        status = result["status"]
        if status == "ready":
            proposed.update(result["entries"])
        elif status == "rejected":
            rejected[code] = {**row, "reason": result.get("reason")}
        else:
            leftover[code] = {**row, "reason": result.get("reason")}

    report = {
        "due": True,
        "pending": len(pending),
        "threshold": GROW_THRESHOLD,
        "proposed": proposed,
        "rejected": rejected,
        "leftover": leftover,
    }
    _write_json(PROPOSED_PATH, {
        "proposed": proposed,
        "rejected": rejected,
        "leftover": leftover,
    })
    return report


def apply_proposed(additives_path: Path | None = None, proposed: dict | None = None) -> int:
    path = additives_path or ADDITIVES_PATH
    db = load_additives_db(path)
    if proposed is None:
        blob = _load_json(PROPOSED_PATH, {})
        proposed = blob.get("proposed") or blob
    added = 0
    for key, value in (proposed or {}).items():
        if key in db:
            continue
        db[key] = value
        added += 1
    if added:
        _write_json(path, db)
    return added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote unknown additive codes into knowledge.")
    parser.add_argument("--force", action="store_true", help="Run even if fewer than 100 unknowns (an engine update).")
    parser.add_argument("--apply", action="store_true", help="Merge proposed entries into additives.json.")
    args = parser.parse_args(argv)

    report = propose_growth(force=args.force)
    if not report["due"]:
        print(
            f"Growth not due: {report['pending']} unique unknowns "
            f"(threshold {report['threshold']}). Pass --force on an engine update."
        )
        return 0

    print(
        f"Pending {report['pending']}: "
        f"{len(report['proposed'])} proposed keys, "
        f"{len(report['rejected'])} rejected, "
        f"{len(report['leftover'])} leftover for LLM."
    )
    if args.apply:
        added = apply_proposed(proposed=report["proposed"])
        print(f"Applied {added} new keys to {ADDITIVES_PATH.name}. Restart the API to load them.")
    else:
        print(f"Wrote {PROPOSED_PATH}. Re-run with --apply to merge into additives.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
