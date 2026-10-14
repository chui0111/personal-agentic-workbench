"""Deterministic processing, review boundary, and local mock synchronization."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REQUIRED = ("company", "title", "source_url", "description")
PROTECTED = frozenset({"application_stage", "application_date", "final_result"})
STATES = frozenset({"CAPTURED", "PARSED", "NEEDS_REVIEW", "SELECTED", "REJECTED", "SYNC_PENDING", "SYNCED", "FAILED"})


def canonical_url(value: str) -> str:
    """Normalize exact web identity, excluding fragments and tracking parameters."""
    if not isinstance(value, str):
        raise ValueError("source_url must be a string")
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    host = parts.hostname.lower()
    port = parts.port
    if port and not ((parts.scheme.lower() == "https" and port == 443) or (parts.scheme.lower() == "http" and port == 80)):
        host += f":{port}"
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                           if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}))
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host, path, query, ""))


def stable_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()[:16]


def validate_job(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("job must be an object")
    for key in REQUIRED:
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f"missing or invalid {key}")
    if not isinstance(value.get("city", ""), str):
        raise ValueError("city must be a string")
    job = {key: value[key].strip() for key in REQUIRED}
    job["city"] = value.get("city", "").strip()
    job["source_url"] = canonical_url(job["source_url"])
    job["id"] = stable_id(job["source_url"])
    job["ambiguous"] = value.get("ambiguous", False) is True
    job["deadline"] = value.get("deadline")
    if job["deadline"] is not None:
        try:
            date.fromisoformat(job["deadline"])
        except (TypeError, ValueError) as exc:
            raise ValueError("deadline must be ISO date or null") from exc
    return job


def atomic_json(path: Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".pending-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_json(path: Path, default: object = None) -> object:
    if not Path(path).exists():
        return default
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def append_attempt(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


class MockAgent:
    """A deterministic stand-in for semantic advice, not an LLM."""

    def analyze(self, job: dict) -> dict:
        text = (job["title"] + " " + job["description"]).lower()
        family = "data" if "data" in text or "analysis" in text else "product" if "product" in text else "operations"
        return {
            "role_family": family,
            "fit_summary": f"Review {family} responsibilities against the fictional candidate profile.",
            "priority_suggestion": "high" if family in {"data", "product"} else "normal",
            "missing_requirements": ["Confirm detailed requirements with a human"],
            "reason": "Keyword-based fixture suggestion only; no private résumé analysis.",
            "review_recommendation": "human_review",
        }


class LocalMockSink:
    """File-backed mock sink with idempotent upsert and protected user fields."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def read(self, record_id: str) -> dict | None:
        return load_json(self.path, {}).get(record_id)

    def upsert(self, record: dict, *, fail_after_write: bool = False) -> dict:
        data = load_json(self.path, {})
        old = data.get(record["id"])
        merged = dict(old or {})
        merged.update({k: v for k, v in record.items() if k not in PROTECTED})
        if old:
            merged.update({k: old[k] for k in PROTECTED if k in old})
        data[record["id"]] = merged
        atomic_json(self.path, data)
        if fail_after_write:
            # A simulated corrupt/missing read-back: undo only this write.
            atomic_json(self.path, {**data, **({record["id"]: old} if old else {})} if old else
                        {k: v for k, v in data.items() if k != record["id"]})
            raise RuntimeError("simulated read-back failure; compensating rollback complete")
        actual = self.read(record["id"])
        if actual != merged:
            atomic_json(self.path, {**data, **({record["id"]: old} if old else {})} if old else
                        {k: v for k, v in data.items() if k != record["id"]})
            raise RuntimeError("read-back mismatch; compensating rollback complete")
        return actual


class Pipeline:
    """Checkpointed pipeline; only explicit human-approved IDs can reach the sink."""

    def __init__(self, workdir: Path, agent: MockAgent | None = None):
        self.workdir = Path(workdir)
        self.agent = agent or MockAgent()
        self.checkpoint = self.workdir / "checkpoint.json"
        self.attempts = self.workdir / "attempts.jsonl"
        self.sink = LocalMockSink(self.workdir / "mock_sink.json")
        self.state = load_json(self.checkpoint, {"records": {}, "errors": []})

    def _save(self) -> None:
        atomic_json(self.checkpoint, self.state)

    def ingest(self, raw: object) -> dict:
        try:
            job = validate_job(raw)
        except ValueError as exc:
            self.state["errors"].append(str(exc))
            append_attempt(self.attempts, {"action": "ingest", "result": "invalid", "error": str(exc)})
            self._save()
            return {"state": "FAILED", "error": str(exc)}
        rid = job["id"]
        if rid in self.state["records"]:
            append_attempt(self.attempts, {"action": "ingest", "result": "duplicate", "id": rid})
            return {"state": "DUPLICATE", "id": rid}
        state = "NEEDS_REVIEW" if job["ambiguous"] else "PARSED"
        entry = {"job": job, "state": state, "analysis": self.agent.analyze(job)}
        self.state["records"][rid] = entry
        self._save()
        append_attempt(self.attempts, {"action": "ingest", "result": state, "id": rid})
        return {"state": state, "id": rid}

    def decide(self, record_id: str, approved: bool) -> None:
        entry = self.state["records"][record_id]
        if entry["state"] not in {"PARSED", "NEEDS_REVIEW", "SELECTED", "SYNC_PENDING"}:
            raise ValueError("record cannot be reviewed from current state")
        entry["state"] = "SELECTED" if approved else "REJECTED"
        self._save()
        append_attempt(self.attempts, {"action": "human_review", "result": entry["state"], "id": record_id})

    def sync(self, record_id: str, *, fail_after_write: bool = False) -> dict:
        entry = self.state["records"][record_id]
        if entry["state"] not in {"SELECTED", "SYNC_PENDING", "SYNCED"}:
            raise ValueError("explicit human approval required")
        entry["state"] = "SYNC_PENDING"
        self._save()
        try:
            result = self.sink.upsert(entry["job"], fail_after_write=fail_after_write)
        except Exception as exc:
            append_attempt(self.attempts, {"action": "sync", "result": "retry_pending", "id": record_id,
                                           "error": type(exc).__name__})
            raise
        entry["state"] = "SYNCED"
        self._save()
        append_attempt(self.attempts, {"action": "sync", "result": "read_back_verified", "id": record_id})
        return result


def build_brief(entries: dict, *, today: date) -> str:
    selected = list(entries.values())
    high = sum(1 for e in selected if e.get("analysis", {}).get("priority_suggestion") == "high")
    upcoming = sum(1 for e in selected if e.get("job", {}).get("deadline") and
                   0 <= (date.fromisoformat(e["job"]["deadline"]) - today).days <= 7)
    review = sum(1 for e in selected if e.get("state") == "NEEDS_REVIEW")
    synced = sum(1 for e in selected if e.get("state") == "SYNCED")
    return (f"Daily Brief ({today.isoformat()})\n"
            f"- {high} high-priority suggestions\n- {upcoming} deadlines within 7 days\n"
            f"- {review} review-needed items\n- pipeline health: {synced} read-back-verified syncs\n")
