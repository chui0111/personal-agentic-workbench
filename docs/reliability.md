# Reliability design

The public Python workbench demonstrates reliability against synthetic inputs and a local mock sink. The historical collector and later Node.js/Playwright reconstruction are private; their implementation is not disclosed here.

| Failure mode | Detection and mitigation | Public evidence |
|---|---|---|
| Duplicate or malformed input | Canonical URLs produce stable IDs; invalid input is rejected and duplicates are identified | `src/personal_agentic_workbench/core.py`; workflow tests |
| Ambiguous recommendation | Analysis advice does not grant approval; uncertain input enters `NEEDS_REVIEW` | Pipeline tests and synthetic demo |
| Interrupted local processing | Atomic checkpoint replacement and append-only attempt logging preserve a resumable state | Workflow tests and failure/recovery demo |
| Local sink write differs from expectation | Read-back precedes `SYNCED`; a mismatch triggers compensating rollback and leaves `SYNC_PENDING` for retry | Workflow tests and failure/recovery demo |

The private reconstruction was separately tested offline: 20 tests passed; its three-record synthetic browser demo matched the expected count and reached the end; CSV export and six leading-character formula-injection cases were validated. Its implementation is intentionally excluded as commercially valuable workflow IP. These results are not evidence of a current live Feishu run, and the public mock sink does not provide remote transactions or distributed exactly-once delivery.
