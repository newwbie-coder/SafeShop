from pathlib import Path

from backend.additive_growth import (
    GROW_THRESHOLD,
    apply_proposed,
    classify_code,
    growth_due,
    log_unknown_additive,
    pending_unknowns,
    propose_growth,
)


def test_queue_counts_unique_codes(tmp_path, monkeypatch):
    queue = tmp_path / "unknown_additives.json"
    monkeypatch.setattr("backend.additive_growth.QUEUE_PATH", queue)
    monkeypatch.setattr("backend.additive_growth.LEGACY_TXT_PATH", tmp_path / "missing.txt")

    log_unknown_additive("ins1422")
    log_unknown_additive("INS1422")
    log_unknown_additive("ins5000")

    pending = pending_unknowns(db={})
    assert pending["ins1422"]["count"] == 2
    assert pending["ins5000"]["count"] == 1
    assert len(pending) == 2


def test_growth_waits_for_100_unless_forced():
    pending = {f"ins{100 + i}": {"count": 1} for i in range(GROW_THRESHOLD - 1)}
    assert growth_due(pending, force=False) is False
    pending["ins199"] = {"count": 1}
    assert len(pending) == GROW_THRESHOLD
    assert growth_due(pending, force=False) is True
    assert growth_due({ "ins1422": {"count": 1} }, force=True) is True


def test_classify_promotes_codex_and_rejects_parser_junk():
    ready = classify_code("ins1422", db={})
    assert ready["status"] == "ready"
    assert ready["entries"]["ins1422"]["risk"] == "low"
    assert ready["entries"]["ins1422"]["name"] == "Acetylated Distarch Adipate"

    alias = classify_code("ins500i", db={"ins500": {"name": "Sodium Carbonate", "risk": "low"}})
    assert alias["status"] == "ready"
    assert alias["entries"]["ins500i"]["ref"] == "ins500"

    junk = classify_code("ins5000", db={})
    assert junk["status"] == "rejected"
    letter = classify_code("ins100g", db={})
    assert letter["status"] == "rejected"


def test_propose_and_apply_only_when_due(tmp_path, monkeypatch):
    queue = tmp_path / "unknown_additives.json"
    proposed = tmp_path / "additives_proposed.json"
    additives = tmp_path / "additives.json"
    additives.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("backend.additive_growth.QUEUE_PATH", queue)
    monkeypatch.setattr("backend.additive_growth.LEGACY_TXT_PATH", tmp_path / "missing.txt")
    monkeypatch.setattr("backend.additive_growth.PROPOSED_PATH", proposed)
    monkeypatch.setattr("backend.additive_growth.ADDITIVES_PATH", additives)

    log_unknown_additive("ins1422")
    log_unknown_additive("ins5000")
    waiting = propose_growth(force=False)
    assert waiting["due"] is False
    assert waiting["pending"] == 2

    report = propose_growth(force=True)
    assert report["due"] is True
    assert "ins1422" in report["proposed"]
    assert "ins5000" in report["rejected"]
    added = apply_proposed(additives_path=additives, proposed=report["proposed"])
    assert added >= 1
    db = __import__("json").loads(additives.read_text(encoding="utf-8"))
    assert db["ins1422"]["risk"] == "low"
    assert "ins5000" not in db
    assert Path(proposed).is_file()
