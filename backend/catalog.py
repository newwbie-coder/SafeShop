"""In-memory product catalog: scrape first, then runtime-learned rows.

Lookup is by product_id or brand+name. We store raw ingredients/nutrition and
always score with the current engine so cache hits never freeze old scores.
"""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RUNTIME_PATH = DATA_DIR / "runtime_catalog.jsonl"

_lock = threading.Lock()
_loaded = False
_by_id: dict[str, dict] = {}
_by_key: dict[str, dict] = {}


def _norm_key(*parts: str) -> str:
    blob = " ".join(p or "" for p in parts).lower()
    blob = re.sub(r"[^a-z0-9]+", " ", blob)
    return re.sub(r"\s+", " ", blob).strip()


def _catalog_paths() -> list[Path]:
    paths = []
    env = os.environ.get("SAFESHOP_CATALOG_PATH", "").strip()
    if env:
        paths.append(Path(env))
        paths.append(RUNTIME_PATH)
    else:
        paths.append(DATA_DIR / "catalog.jsonl")
        paths.append(Path(r"D:\safeshopV2\safeshop\data\safeshop_dataset.jsonl"))
        paths.append(RUNTIME_PATH)

    seen = set()
    unique = []
    for path in paths:
        resolved = str(path.resolve()) if path.exists() else str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _ingest_row(row: dict, source: str) -> None:
    product_id = str(row.get("product_id") or "").strip()
    name = (row.get("name") or "").strip()
    brand = (row.get("brand") or "").strip()
    ingredients = row.get("ingredients") or ""
    if isinstance(ingredients, list):
        ingredients = ", ".join(str(x) for x in ingredients)
    nutrition = row.get("nutrition") or row.get("nutrition_text") or ""

    if not name and not product_id:
        return
    if not str(ingredients).strip() and not str(nutrition).strip():
        return

    record = {
        "product_id": product_id,
        "name": name,
        "brand": brand,
        "ingredients": str(ingredients),
        "nutrition": str(nutrition),
        "source": source,
    }
    if product_id:
        _by_id[product_id] = record
    key = _norm_key(brand, name)
    if key:
        _by_key[key] = record
    name_key = _norm_key(name)
    if name_key and name_key not in _by_key:
        _by_key[name_key] = record


def reset_for_tests() -> None:
    global _loaded
    with _lock:
        _loaded = False
        _by_id.clear()
        _by_key.clear()


def load_catalog(force: bool = False) -> None:
    global _loaded
    with _lock:
        if _loaded and not force:
            return
        _by_id.clear()
        _by_key.clear()
        for path in _catalog_paths():
            if not path.is_file():
                continue
            source = path.name
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        _ingest_row(json.loads(line), source)
                    except Exception:
                        continue
        _loaded = True


def lookup(product_id: str | None = None, brand: str | None = None, name: str | None = None) -> dict | None:
    load_catalog()
    pid = str(product_id or "").strip()
    if pid and pid in _by_id:
        return _by_id[pid]
    key = _norm_key(brand or "", name or "")
    if key and key in _by_key:
        return _by_key[key]
    name_key = _norm_key(name or "")
    if name_key and name_key in _by_key:
        return _by_key[name_key]
    return None


def remember(product_id: str | None, brand: str | None, name: str | None, ingredients: str, nutrition: str) -> None:
    """Grow the runtime catalog from live analyses that had real label text."""
    if not (ingredients or "").strip() and not (nutrition or "").strip():
        return
    if not (name or "").strip() and not (product_id or "").strip():
        return

    row = {
        "product_id": str(product_id or "").strip(),
        "name": (name or "").strip(),
        "brand": (brand or "").strip(),
        "ingredients": ingredients or "",
        "nutrition": nutrition or "",
    }
    load_catalog()
    with _lock:
        _ingest_row(row, "runtime")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with RUNTIME_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
