"""Show rollback, preserved pending state, checkpoint reload, and retry."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from personal_agentic_workbench import Pipeline  # noqa: E402


def main() -> None:
    raw = json.loads((ROOT / "examples" / "synthetic_jobs.json").read_text(encoding="utf-8"))[0]
    (ROOT / "demo-output").mkdir(exist_ok=True)
    with TemporaryDirectory(dir=ROOT / "demo-output") as location:
        location = Path(location)
        pipeline = Pipeline(location)
        rid = pipeline.ingest(raw)["id"]
        pipeline.decide(rid, approved=True)
        try:
            pipeline.sync(rid, fail_after_write=True)
        except RuntimeError:
            pass
        print("Simulated read-back failure: sink rolled back; pending preserved =",
              pipeline.state["records"][rid]["state"] == "SYNC_PENDING" and pipeline.sink.read(rid) is None)
        resumed = Pipeline(location)
        resumed.sync(rid)
        print("Checkpoint resume + retry: read-back verified =",
              resumed.state["records"][rid]["state"] == "SYNCED" and resumed.sink.read(rid) is not None)


if __name__ == "__main__":
    main()
