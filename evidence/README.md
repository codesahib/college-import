# Evidence index

All data and operator labels are synthetic. Generated results record actual execution, not illustrative numbers. Rerunning verification replaces generated reports/screenshots with the current run.

| Artifact | Origin / scope |
|---|---|
| `baseline-diagnosis.json` | `python scripts/diagnose.py`; original parser against all six fixtures, captured before improvement |
| `benchmark.json` | `python scripts/benchmark.py`; API-based baseline/after comparison, fixture/oracle hashes, initial/final runs, canonical oracle checks and replay assertions |
| `verification.json` | `python scripts/verify.py`; actual commands, exit codes, stdout/stderr, platform and selected browser channel |
| `backend-tests.xml` | pytest JUnit output, 31 tests |
| `playwright-results.json` | Playwright's native JSON output, 2 browser scenarios |
| `reset-output.txt` | Actual repeated reset/seed execution output; stable counts and pending-review state |
| `01-baseline.png` | Original contract accepts Atlas v1; changed Atlas is rejected |
| `02-normalized.png` | Changed Atlas normalization, live counts, precise missing-ID explanation and canonical rows |
| `03-quarantine.png` | Ambiguous year fields held with source samples and unresolved selection |
| `04-approved-replay.png` | Approved mapping reused on exact file replay without record growth |
| `05-registry.png` | Configured contracts and operator approval log |
| `06-mobile.png` | Unknown schema review on a 390px mobile viewport, no whole-page horizontal overflow |

Browser screenshots use an empty dedicated smoke database and a subset of fixtures. They show 3 then 5 improved records, not the full benchmark's 14. Reset/seed shows 12 improved records before approval. `benchmark.json` shows 14 after one simulated approval. These are different declared scenario states, not fixed UI counters.

Baseline gate: 3 backend tests and frontend production build passed before commit/tag. Final verification: 31 backend tests, TypeScript check, production build, benchmark assertions and 2 browser tests pass. Tests emit a Starlette TestClient deprecation warning. Chromium download initially failed with ENOSPC; installed Chrome provided successful browser execution. A Windows console Unicode issue in the new check runner was fixed before the successful final run. Ubuntu/WSL commands are documented; captured execution is native Windows.

Git provenance: `615da24` baseline / `baseline-demo`, `33f5cdf` diagnosis, `0b8aa19` improvement. Subsequent evaluation/handoff commits contain these generated artifacts and documentation. `git diff baseline-demo -- backend/parser.py` is empty: the strict parser used for comparison has not changed.
