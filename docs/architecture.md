# Architecture and responsibility boundary

| Actor | Owns | Never owns |
|---|---|---|
| Deterministic code | parsing, schema validation, URL normalization, exact deduplication, stable IDs, checkpointing, state transitions, mock sync, read-back | subjective hiring fit or silent approval |
| Analysis provider | fit summary, role-family suggestion, missing-requirement prompts, explanation | data integrity, final application decisions |
| Human reviewer | ambiguous cases, approval/rejection, high-risk external actions | machine-generated facts without checking |

The `MockAgent.analyze` method is an intentionally deterministic stand-in for a semantic provider. Its output schema allows a future provider but the published demo has no paid API dependency. The `Pipeline` prevents unapproved records from entering the sink. Ambiguous input enters `NEEDS_REVIEW`, never silent approval.

Input → validated raw record → canonical URL / stable ID → advice → human decision → local mock sync → read-back → brief. Atomic checkpoint and append-only attempts surround the processing and sync boundary.
