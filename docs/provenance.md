# Provenance and evidence limits

This project has **three distinct stages**, not one continuously deployed codebase.

1. **Historical real workflow (September 2026).** A recovered, host-mediated browser code excerpt reads rendered Feishu Base record-detail cards. It returns `recordId`, `title`, `fields` (including per-field links), and `nextDisabled`; the recovered batch checks 14 fields and records `expectedCount:7155`. Historical notes report segmented collection and a validated 7,155-record merge. The complete original conversation, raw browser segments, and merge report are **not** included here, so execution totals are reported as historical evidence, not independently rerun facts.
2. **Private engineering reconstruction (October 2026).** A later, standalone Node.js/Playwright study project reconstructed the collection workflow. Its original ZIP was hash-checked (18/18 manifest entries). The implementation is intentionally excluded from this public portfolio because it contains commercially valuable workflow IP. Local validation found 20 passing tests; an offline synthetic demo collected three unique records with 14 fields each, matched the expected count, and reached the end. JSON-to-CSV export and formula-injection protection for `=`, `+`, `-`, `@`, TAB, and CR were also verified. These tests do not validate live Feishu behavior.
3. **Personal Agentic Workbench (this repository).** The Python demo uses synthetic data to show normalization, analysis-advice boundaries, human approval, an idempotent local sink, read-back verification, and recovery. It does not publish the private Feishu integration or claim autonomous LLM operation.

## Claim / evidence matrix

`CONFIRMED` means directly visible in recovered code or a local test; `SUPPORTED` means a recovered narrative/report says it happened but the underlying historical data is absent.

| Claim | Recovered evidence and location | Status | Limit |
|---|---|---|---|
| Rendered DOM extraction | Private historical code excerpt | CONFIRMED in excerpt | Current live site not tested |
| `recordId`, `title`, `fields`, `links`, `nextDisabled` extracted | Same private historical excerpt | CONFIRMED in excerpt | Full original source/session absent |
| Historical 14-field check and title/first-field consistency | Private historical validation excerpt | CONFIRMED in excerpt | Exact 14 historical field names not recovered |
| Historical `expectedCount:7155` | Private historical collection excerpt | CONFIRMED in excerpt | An expected count is not a completed-count proof |
| Historical 7,155 collected records and unique Feishu IDs | Private historical validation notes | SUPPORTED | Raw segment records/ID audit absent |
| 8 browser segments and 7 overlaps | Private historical completion notes | SUPPORTED | Original segment files/merge report absent; distinct from local text-split chunks |
| No positional gaps after historical merge | Private historical validation notes | SUPPORTED | Original positional validation output absent |
| Local source export has 7,155 indexed records | Separate local export verification | CONFIRMED separately | Does not prove 7,155 browser page visits or historical Feishu ID uniqueness |
| Private reconstruction tests and three-card demo | Local private validation; implementation excluded | CONFIRMED | Synthetic page only; no public implementation |
| Python workbench reliability behavior | `tests/test_workflow.py` and offline demos in this repository | CONFIRMED | Local mock sink, not live Feishu |

## Publication classification

| Component | Classification | Public boundary |
|---|---|---|
| Python processing pipeline and tests | PUBLIC IMPLEMENTATION | Synthetic inputs and local mock sink only |
| Python fixture and offline demos | SYNTHETIC PUBLIC DEMO | No production recruiting records or live Feishu access |
| Later Node.js/Playwright reconstruction | PRIVATE VERIFIED IMPLEMENTATION | Local validation results may be reported; source and implementation-specific logic are withheld as commercially valuable workflow IP |
| Historical browser-code excerpt, execution notes and raw evidence | HISTORICAL EVIDENCE ONLY | Summarized with evidence limits; original code, raw segments and private identifiers are not published |

The later private reconstruction is not byte-for-byte original code. Its validation results must not be retroactively attributed to the historical 7,155-record run. Missing private source is an intentional publication boundary, not an accidental omission.
