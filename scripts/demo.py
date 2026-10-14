"""Run a credentials-free, temporary-directory demonstration."""

from datetime import date
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from personal_agentic_workbench import Pipeline, build_brief  # noqa: E402
from personal_agentic_workbench.collector import extract_fixture_html  # noqa: E402


def main() -> None:
    fixture = extract_fixture_html((ROOT / "examples" / "synthetic_page.html").read_text(encoding="utf-8"))
    raw_jobs = json.loads((ROOT / "examples" / "synthetic_jobs.json").read_text(encoding="utf-8"))
    (ROOT / "demo-output").mkdir(exist_ok=True)
    with TemporaryDirectory(dir=ROOT / "demo-output") as location:
        pipeline = Pipeline(Path(location))
        results = [pipeline.ingest(job) for job in raw_jobs]
        # This explicit set simulates a person's approval; suggestions do not auto-approve.
        approved = [r["id"] for r in results if r["state"] == "PARSED"][:3]
        for record_id in approved:
            pipeline.decide(record_id, approved=True)
            pipeline.sync(record_id)
        print("Personal Agentic Workbench — synthetic offline demo")
        print(f"Collector fixture: {fixture['company']} / {fixture['title']}")
        print(f"Input: {len(raw_jobs)}; parsed: {sum(r['state'] == 'PARSED' for r in results)}; "
              f"duplicate: {sum(r['state'] == 'DUPLICATE' for r in results)}; "
              f"review: {sum(r['state'] == 'NEEDS_REVIEW' for r in results)}; "
              f"malformed: {sum(r['state'] == 'FAILED' for r in results)}")
        example = pipeline.state["records"][approved[0]]
        print(f"Analysis suggestion: {example['analysis']['role_family']} / "
              f"{example['analysis']['priority_suggestion']} (human review required)")
        print(f"Human-approved, synced, read-back verified: {len(approved)}")
        print(f"Final state: {sum(e['state'] == 'SYNCED' for e in pipeline.state['records'].values())} SYNCED; "
              f"{sum(e['state'] == 'NEEDS_REVIEW' for e in pipeline.state['records'].values())} NEEDS_REVIEW")
        print(build_brief(pipeline.state["records"], today=date(2026, 12, 19)), end="")


if __name__ == "__main__":
    main()
