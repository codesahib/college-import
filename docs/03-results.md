# Evaluation: measured results

Source of truth: [`evidence/benchmark.json`](../evidence/benchmark.json). Captured on 2026-11-07 UTC (2026-11-06 Toronto), Windows 11, Python 3.13.14. No customer data or systems were used.

## Method

`python scripts/benchmark.py` creates one fresh repository-local temporary SQLite database. Workflow is part of the record/file keys, so baseline and improved receive identical CSV bytes with isolated records. Each of the six files is uploaded once per workflow via FastAPI TestClient. Fixtures and oracle are SHA-256 hashed in the report. Both workflows receive the same declared ground truth from `fixtures/expected.json`: 19 rows, 15 valid, 4 invalid.

The baseline is the unchanged `parse_baseline` from tag `baseline-demo`. Improved detection first processes all six files without operator intervention (12 valid rows accepted, 3 valid rows held in 2 schemas). The script then submits **one** explicit approval for `ambiguous_v3.csv`, mapping application year and acknowledging ignored graduation year. The unknown file is not approved. Final accepted canonical dictionaries are compared to oracle IDs, years, decisions, and dates. Row accounting must balance. Rejected invalid counts come from actual rejected counts minus rejected valid rows. Every file is replayed, asserting the same record list and no extra run creation.

These are exact fixture counts from a single deterministic scenario, not statistical estimates. Timings, human engineering effort, support-ticket volumes, and human-only team performance were not measured. There is no runtime performance improvement claim.

## Per-file outcomes

`A / R / H` means valid rows accepted / rejected / held. Invalid rows are separate.

| File | Valid / invalid | Baseline valid A/R/H | Improved valid A/R/H | Baseline / improved invalid rejected | Final improved mapping |
|---|---:|---:|---:|---:|---|
| Atlas v1 | 3 / 1 | 3 / 0 / 0 | 3 / 0 / 0 | 1 / 1 | Atlas@1 |
| Birch v1 | 3 / 1 | 0 / 3 / 0 | 3 / 0 / 0 | 1 / 1 | Birch@1 |
| Cedar v1 | 3 / 1 | 0 / 3 / 0 | 3 / 0 / 0 | 1 / 1 | Cedar@1 |
| Atlas v2, changed | 3 / 1 | 0 / 3 / 0 | 3 / 0 / 0 | 1 / 1 | Aliases@1 |
| Ambiguous v3 | 2 / 0 | 0 / 2 / 0 | 2 / 0 / 0 | 0 / 0 | Atlas reviewed@1, after approval |
| Unknown v1 | 1 / 0 | 0 / 1 / 0 | 0 / 0 / 1 | 0 / 0 | Unassigned, held |
| **Total** | **15 / 4** | **3 / 12 / 0** | **14 / 0 / 1** | **4 / 4** | |

Valid-row acceptance changes from 20% to 93.3% for this dataset. Without the approval it is 12/15 (80%). The remaining valid row is a transparent unresolved contract, not a row-validation failure. Holding that row does not count as accepting it.

## Schema/action and regression evidence

| Measure | Baseline | Improved | Interpretation |
|---|---:|---:|---|
| Required initial correction events | 5 | 2 | 60% fewer distinct schemas need intervention on these fixtures |
| Actual operator approvals executed | 0 | 1 | No baseline code corrections were performed in the benchmark |
| Noncanonical schemas visibly surfaced | 5 / 5 | 5 / 5 | Both detect departures; improved known formats can proceed safely |
| Ambiguous/unknown schemas quarantined initially | 0 / 2 | 2 / 2 | Baseline rejects these schemas outright instead |
| Incorrect silent canonical mappings | 0 | 0 | Full accepted-row dictionaries match the oracle |
| Four supported-format criteria met | 1 / 4 | 4 / 4 | Original + Birch + Cedar + changed Atlas; all valid rows accepted, invalid rejected |
| Stored records before → after replay | 3 → 3 | 14 → 14 | Zero record growth, all six replays reuse their existing runs |

One correction event means one distinct schema needing an engineering mapper change (baseline) or a submitted mapping configuration (improved), regardless of how many UI fields/clicks it uses. Initial requirements are derived from observed `schema_error`/`awaiting_review` statuses and checked against the declared scenario. Baseline 5 is a count of required future corrections, not five executed edits. Improved 2 includes the unresolved unknown schema, so it is not a claim of two completed approvals.

All five header departures produce a baseline header-level report and an improved drift indicator. The actual uncertain schema errors are application-year ambiguity and unrecognized ID/date columns: improved reports the candidate year names and missing field mappings and holds both files. The four invalid-row explanations after normalization identify source columns: `year`, Birch `decision_date`, Cedar `verdict`, and changed Atlas `student_key`. Inspect `initial_runs` and `final_runs` in the raw report for all messages, values, row numbers, mapping snapshots, and counts.

Format regression criteria are distinct from test-suite pass counts. All **3 baseline tests passed** at the baseline gate because they encode the original contract and its known shortcoming. The final **31 backend tests passed**, including that baseline coverage, the four vendor regressions, approval atomicity, header edge cases, incorrect-date rejection, conservative graduation-year handling, identity conflicts, and concurrent replay. **2 Playwright tests passed**, covering the UI path and mobile quarantine. Typecheck and production build passed. Actual exit codes/output: [`verification.json`](../evidence/verification.json); machine-readable test details: [`backend-tests.xml`](../evidence/backend-tests.xml), [`playwright-results.json`](../evidence/playwright-results.json).

## What did not improve, and limits

- Invalid-row rejection remains 4/4. Baseline header failures already rejected invalid rows; only one of those was diagnosed at row level before normalization.
- Silent mismatches remain zero and replay record growth remains zero. The baseline was already conservative and idempotent. Improvement adds coverage and explicit conflicting-identity explanations.
- Both surfaced all five departures. A drift flag means a header-set departure from the canonical contract; it is not an inference that a known vendor mapping is broken.
- One unknown schema still needs operator knowledge. An operator can approve a syntactically valid but semantically wrong choice. The software does not determine business meaning.
- Six hand-authored tiny fixtures are not representative of enterprise data distributions or scale. Three fictional vendors plus a changed format do not establish broad interoperability. No fuzzing, accessibility certification, production deployment, load benchmark, or independent human usability study was conducted.
- Exact header signatures cannot resolve same-header/different-meaning vendor collisions. Date formats are configured contracts; a silent upstream semantic change can evade detection. Add authenticated vendor identity/contract versions before using this on real sources.
- Browser screenshots cover a smaller empty-database smoke sequence, not the complete benchmark dataset. Their counts reflect live scenario state. Reset/seed intentionally stops before approval (12 improved records); evaluation proceeds to 14 after its simulated approval.
- The bundled Chromium download failed with ENOSPC. Installed Chrome successfully ran the smoke tests. Starlette emits an `httpx` deprecation warning; no failing tests remain. Native Windows validation is evidenced; Ubuntu/WSL commands are documented but not claimed as executed.
