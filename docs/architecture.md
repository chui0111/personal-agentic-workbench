# Architecture and responsibility boundary

The stages are related by an operational problem, not by shared runtime or an uninterrupted deployment history.

```mermaid
flowchart LR
  subgraph H[1. Historical workflow — evidence only]
    H1[Rendered Feishu record card] --> H2[Private browser collection workflow]
    H2 --> H3[Structured historical output]
    H3 --> H4[Merge verification reported in historical notes]
  end
  subgraph R[2. Private engineering reconstruction]
    R1[Offline synthetic input] --> R2[Private Node.js and Playwright workflow]
    R2 --> R3[Locally validated output]
  end
  subgraph W[3. Public Agentic Workbench]
    W1[Synthetic source adapter] --> W2[Normalize, validate, dedupe]
    W2 --> W3[Analysis-advice boundary]
    W3 --> W4{Human approval}
    W4 --> W5[Idempotent local sink]
    W5 --> W6[Read-back, recovery, brief]
  end
```

| Actor | Owns | Never owns |
|---|---|---|
| Deterministic code | parsing, schema validation, URL normalization, exact deduplication, stable IDs, checkpointing, state transitions, mock sync, read-back | subjective hiring fit or silent approval |
| Analysis provider | fit summary, role-family suggestion, missing-requirement prompts, explanation | data integrity, final application decisions |
| Human reviewer | ambiguous cases, approval/rejection, high-risk external actions | machine-generated facts without checking |

The Python `MockAgent.analyze` is an intentionally deterministic stand-in, not an LLM. The Python `Pipeline` prevents unapproved records from entering its local sink. Ambiguous input enters `NEEDS_REVIEW`. The historical and reconstruction stages are shown only at interface level: their private implementation is intentionally withheld. The public workbench runs on synthetic data and has no live Feishu integration.
