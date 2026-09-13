import json
import os

from fastapi.testclient import TestClient

from backend import catalog
from backend.feedback_store import contemplate, record_feedback
from backend.image_fallback import _host_allowed
from backend.main import app


def test_image_host_allowlist():
    assert _host_allowed("https://www.bbassets.com/foo.jpg")
    assert _host_allowed("https://cdn.bbassets.com/a.jpg")
    assert _host_allowed("https://www.bigbasket.com/media/x.jpg")
    assert not _host_allowed("https://evil.example/a.jpg")


def test_contemplate_classifies_lenient_and_strict():
    assert contemplate("this is too healthy")["issue"] == "score_too_lenient"
    assert contemplate("too harsh, should be higher")["issue"] == "score_too_strict"
    assert contemplate("ocr misread the label")["issue"] == "extraction_error"


def test_catalog_lookup_by_name_and_id(tmp_path, monkeypatch):
    catalog_file = tmp_path / "catalog.jsonl"
    catalog_file.write_text(
        json.dumps({
            "product_id": "270510",
            "name": "Schezwan Instant Noodles",
            "brand": "Ching's Secret",
            "ingredients": "Refined Wheat Flour, Palm Oil, Flavour Enhancer (INS 635)",
            "nutrition": "Nutrition_per: 100 g Energy (kcal): 425 Sodium (mg): 1583 "
                         "Carbohydrate (g): 63.8 Protein (g): 11 Total Fat (g): 14",
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SAFESHOP_CATALOG_PATH", str(catalog_file))
    catalog.reset_for_tests()

    hit = catalog.lookup(product_id="270510")
    assert hit["name"] == "Schezwan Instant Noodles"
    by_name = catalog.lookup(brand="Ching's Secret", name="Schezwan Instant Noodles")
    assert by_name["product_id"] == "270510"


def test_analyze_uses_catalog_when_page_has_no_label(tmp_path, monkeypatch):
    catalog_file = tmp_path / "catalog.jsonl"
    catalog_file.write_text(
        json.dumps({
            "product_id": "270510",
            "name": "Schezwan Instant Noodles",
            "brand": "Ching's Secret",
            "ingredients": "Refined Wheat Flour, Palm Oil, Flavour Enhancer (INS 635)",
            "nutrition": "Nutrition_per: 100 g Energy (kcal): 425 Sodium (mg): 1583 "
                         "Carbohydrate (g): 63.8 Protein (g): 11 Total Fat (g): 14 "
                         "Total Sugars (g): 2.6 Added Sugars (g): 2.6 Saturated Fat (g): 7.1",
        }) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SAFESHOP_CATALOG_PATH", str(catalog_file))
    catalog.reset_for_tests()

    client = TestClient(app)
    response = client.post("/analyze", json={
        "name": "Schezwan Instant Noodles",
        "brand": "Ching's Secret",
        "product_id": "270510",
        "ingredients": "",
        "nutrition_text": "",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "cache"
    assert body["needs_ocr"] is False
    assert body["verdict"] == "Unhealthy"


def test_analyze_missing_label_asks_for_ocr(monkeypatch, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("SAFESHOP_CATALOG_PATH", str(empty))
    catalog.reset_for_tests()

    client = TestClient(app)
    response = client.post("/analyze", json={
        "name": "Unknown Snack",
        "ingredients": "",
        "nutrition_text": "",
    })
    body = response.json()
    assert body["needs_ocr"] is True
    assert body["source"] == "live"
    assert body["verdict"] != "Healthy"


def test_feedback_is_appended(tmp_path, monkeypatch):
    target = tmp_path / "feedback.jsonl"
    monkeypatch.setattr("backend.feedback_store.FEEDBACK_PATH", target)
    row = record_feedback(
        comment="too healthy for instant noodles",
        name="Noodles",
        score_shown=90,
        verdict_shown="Healthy",
    )
    assert row["issue"] == "score_too_lenient"
    saved = json.loads(target.read_text(encoding="utf-8").strip())
    assert saved["name"] == "Noodles"
    assert saved["comment"]


def test_analyze_image_rejects_unknown_host(monkeypatch, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("SAFESHOP_CATALOG_PATH", str(empty))
    catalog.reset_for_tests()

    client = TestClient(app)
    response = client.post("/analyze_image", json={
        "name": "Unknown Snack",
        "image_url": "https://evil.example/label.jpg",
    })
    assert response.status_code == 400
    assert response.json()["error"] is True


def test_analyze_image_scores_extracted_text(monkeypatch, tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("SAFESHOP_CATALOG_PATH", str(empty))
    monkeypatch.setattr("backend.catalog.RUNTIME_PATH", tmp_path / "runtime.jsonl")
    catalog.reset_for_tests()

    def fake_ocr(**kwargs):
        return {
            "raw_text": (
                "Ingredients: refined wheat flour, palm oil. "
                "Nutrition: Energy 425 kcal Sodium 1583 mg Protein 11 g"
            ),
            "ingredients": "refined wheat flour, palm oil",
            "nutrition_text": "energy 425 kcal sodium 1583 mg protein 11 g",
            "ocr_confidence": 0.9,
            "confidence": 0.8,
        }

    monkeypatch.setattr("backend.image_fallback.ocr_label_image", fake_ocr)
    client = TestClient(app)
    response = client.post("/analyze_image", json={
        "name": "Test Noodles",
        "product_id": "999",
        "image_url": "https://www.bbassets.com/label.jpg",
    })
    assert response.status_code == 200
    body = response.json()
    assert not body.get("error")
    assert body["source"] == "ocr"
    assert body["needs_ocr"] is False
    assert body["score"] < 70
