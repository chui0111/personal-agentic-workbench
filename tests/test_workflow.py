import json
from pathlib import Path

import pytest

from personal_agentic_workbench import (LocalMockSink, Pipeline, atomic_json,
                                        canonical_url, load_json, stable_id, validate_job)
from personal_agentic_workbench.collector import extract_fixture_html, extract_with_playwright

ROOT = Path(__file__).resolve().parents[1]
JOBS = json.loads((ROOT / "examples" / "synthetic_jobs.json").read_text(encoding="utf-8"))


def test_schema_valid_and_malformed():
    assert validate_job(JOBS[0])["company"] == "Cedar Orbit Labs"
    with pytest.raises(ValueError, match="source_url"):
        validate_job(JOBS[-1])


def test_canonical_url_and_duplicate(tmp_path):
    assert canonical_url(JOBS[0]["source_url"]) == canonical_url(JOBS[-2]["source_url"])
    p = Pipeline(tmp_path)
    assert p.ingest(JOBS[0])["state"] == "PARSED"
    assert p.ingest(JOBS[-2])["state"] == "DUPLICATE"
    assert len(p.state["records"]) == 1


def test_ambiguous_requires_human_review(tmp_path):
    p = Pipeline(tmp_path)
    result = p.ingest(JOBS[-3])
    assert result["state"] == "NEEDS_REVIEW"
    with pytest.raises(ValueError, match="approval"):
        p.sync(result["id"])


def test_atomic_write_and_checkpoint_resume(tmp_path):
    path = tmp_path / "atomic.json"
    atomic_json(path, {"valid": True})
    assert load_json(path) == {"valid": True}
    assert not list(tmp_path.glob("*.tmp"))
    p = Pipeline(tmp_path)
    rid = p.ingest(JOBS[0])["id"]
    q = Pipeline(tmp_path)
    assert q.state["records"][rid]["state"] == "PARSED"
    assert q.ingest(JOBS[0])["state"] == "DUPLICATE"


def test_idempotent_sync_and_protected_fields(tmp_path):
    sink = LocalMockSink(tmp_path / "sink.json")
    item = validate_job(JOBS[0])
    sink.upsert(item)
    data = load_json(sink.path)
    data[item["id"]]["application_stage"] = "human-confirmed"
    atomic_json(sink.path, data)
    altered = dict(item, title="Updated", application_stage="machine-overwrite")
    assert sink.upsert(altered)["application_stage"] == "human-confirmed"
    assert len(load_json(sink.path)) == 1
    assert sink.upsert(altered) == sink.read(item["id"])


def test_readback_failure_rollback_pending_and_recovery(tmp_path):
    p = Pipeline(tmp_path)
    rid = p.ingest(JOBS[0])["id"]
    p.decide(rid, True)
    with pytest.raises(RuntimeError, match="rollback"):
        p.sync(rid, fail_after_write=True)
    assert p.state["records"][rid]["state"] == "SYNC_PENDING"
    assert p.sink.read(rid) is None
    q = Pipeline(tmp_path)
    assert q.sync(rid)["id"] == rid
    assert q.state["records"][rid]["state"] == "SYNCED"
    assert len((tmp_path / "attempts.jsonl").read_text(encoding="utf-8").splitlines()) >= 4


def test_actual_readback_mismatch_rolls_back(tmp_path, monkeypatch):
    sink = LocalMockSink(tmp_path / "sink.json")
    item = validate_job(JOBS[0])
    monkeypatch.setattr(sink, "read", lambda record_id: {"id": record_id, "unexpected": True})
    with pytest.raises(RuntimeError, match="read-back mismatch"):
        sink.upsert(item)
    assert load_json(sink.path) == {}


def test_synthetic_html_extraction():
    html = (ROOT / "examples" / "synthetic_page.html").read_text(encoding="utf-8")
    job = extract_fixture_html(html)
    assert job["title"] == "Data Product Associate"
    assert job["source_url"] == "https://example.com/jobs/cedar-data-product"


def test_optional_playwright_synthetic_fixture():
    pytest.importorskip("playwright.sync_api")
    try:
        job = extract_with_playwright(ROOT / "examples" / "synthetic_page.html")
    except Exception as exc:
        if "Executable doesn't exist" in str(exc):
            pytest.skip("Optional Playwright browser binary is not installed")
        raise
    assert job["company"] == "Cedar Orbit Labs"
    assert job["source_url"] == "https://example.com/jobs/cedar-data-product"


def test_stable_id():
    assert stable_id(JOBS[0]["source_url"]) == stable_id(JOBS[-2]["source_url"])
