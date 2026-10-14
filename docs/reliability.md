# Reliability design

- Every accepted record receives a stable hash ID from its canonical HTTP(S) URL. Tracking parameters and fragments are removed; other query parameters remain part of identity.
- Invalid input is logged and excluded. Ambiguity goes to review, not a guessed final decision.
- The checkpoint and mock sink use same-directory temporary files, `fsync`, and `os.replace` for atomic replacement. Raw fixture files are never mutated.
- Attempts are appended as JSON Lines. The checkpoint is saved before sync, leaving `SYNC_PENDING` if a write or read-back fails.
- The local sink performs idempotent upsert and preserves protected application fields already in the sink.
- The sink reads each write back. The failure demo simulates a mismatch and performs a compensating rollback, then reloads the last checkpoint and retries.
- No claim is made that this mock provides transactions across a remote service or distributed exactly-once delivery.
