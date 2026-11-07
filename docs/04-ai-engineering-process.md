# AI-supported engineering process

The operational work comes first: an admissions admin uploads a CSV, support reproduces a failed import, engineering maintains a deterministic contract, and an operator reviews unresolved fields. There is no AI in that runtime path.

## What Codex actually examined

This repository began with `TASK.md` only. Codex read it in full and checked repository status, tool versions, and applicable repository guidance. No existing production code, Beacon logs, real support tickets, or private records were supplied. The baseline is a deliberately narrow, functioning fictional existing system built in this session, not a claim of discovering an acquired company's code.

After committing/tagging the baseline, Codex examined:

- `backend/parser.py`: canonical header-set guard, standard-library CSV decoding, enum/date/year/ID validation. The header-set guard explained why Atlas v2 never reached row validation.
- `fixtures/atlas_v1.csv`, `atlas_v2.csv`, `birch_v1.csv`, `cedar_v1.csv`, `ambiguous_v3.csv`, `unknown_v1.csv`: header differences, enum spellings, declared date contracts, ambiguity and missing aliases.
- `evidence/baseline-diagnosis.json` from `scripts/diagnose.py`: one successful schema and five schema errors, rejecting 12 valid rows.
- `backend/db.py`: record identity and run/file keys; baseline `INSERT OR IGNORE` preserves records but cannot explain conflicting duplicate identities.
- `backend/tests/test_baseline.py`, `test_api_baseline.py`: passing expected baseline behavior and replay semantics.

During implementation it inspected request/error outputs through backend tests, `scripts/benchmark.py`, the browser smoke test, `evidence/verification.json`, and rendered desktop/mobile screenshots. It checked the declarative schema registry, approval payload validation, SQL uniqueness and transaction boundaries against the stated invariants.

## Proposals and engineering review

Review in this exercise means Codex's code/invariant review and executable checks. The user authorized routine implementation choices; there was no independent human code review or measured human comparison. The scenario's UI/benchmark approvals are simulated operator actions and do not represent a real customer's approval.

| Proposed choice | Decision and evidence |
|---|---|
| Keep strict-v1 executable for side-by-side comparison | Accepted. Preserved `backend/parser.py`, its tests, Git tag and workflow-specific record namespaces. |
| Separate contract detection from row validation | Accepted. `normalizer.py` selects an exact declarative signature or conservative complete aliases before validation. Four fixture regressions check canonical values. |
| Treat graduation year as an ordinary unique year alias | Rejected during code review. A sole graduation year would silently import the wrong business meaning. It is review-only; a dedicated regression asserts quarantine. |
| Guess unknown headers or interpret ambiguous dates from values | Rejected. Unknown/extra/ambiguous columns are held; vendor date contracts use three allowlisted formats and round-trip validation. |
| Let an operator approve a mapping instead of editing parser code each time | Accepted with strict one-to-one fields, ignored-column acknowledgement, reviewer, immutable signature/version, transactional writes and API negative tests. |
| Overwrite prior decisions on duplicate applicant/year | Rejected. Improved importer reports conflicts, preserves the first record, and requires external reconciliation. A negative test checks stored values. |
| Add an LLM row parser or customer chatbot | Rejected as unnecessary. Standard CSV parsing, JSON contracts, validation and SQLite constraints solve the demonstrated problem locally. |
| Use separate services/queues/Docker | Rejected for this bounded local vertical slice. FastAPI + SQLite + Vite is sufficient. |

## Specific delivered changes

`backend/normalizer.py` and `mappings.json` add versioned contracts, aliases, format detection and source-column explanations. `main.py` adds approval/reprocessing and atomic conflict-aware persistence. `db.py` adds a unique workflow/file key and the approved mapping registry. `frontend/src/Review.tsx` exposes source samples, source-field selects, date format, ignored columns and consent before submission. The workspace exposes real history, row reports, live counts, drift markers, accepted rows and downloadable JSON reports. Registry approvals retain reviewer/time/version.

Codex wrote regression and negative tests in `backend/tests/test_improvement.py`, browser scenarios in `frontend/e2e/import.spec.ts`, and deterministic reset/diagnosis/benchmark/verification scripts. Checks cover all three vendors and changed Atlas, malformed input, BOM/case/reorder/quoted fields, duplicate headers, wrong dates, missing IDs, invalid approvals, approval reuse, conflict preservation, concurrent replay and unknown schema quarantine.

The operational workflow now sends support a reproducible row/column report and mapping version. Known mappings need no intervention; ambiguous mappings are reviewed once and reused for later files of that signature. A new format can be added as a fixture and declarative contract with regression assertions before release.

## Failures encountered and resolved

The native shell blocked `npm.ps1`; commands used `npm.cmd` on Windows. Bundled Chromium installation failed due to ENOSPC; tests successfully ran against installed Chrome through `PLAYWRIGHT_CHANNEL=chrome`. The first verification-runner attempt could not print Vite's Unicode checkmark to the Windows console; setting UTF-8 stdout fixed it and the full runner subsequently passed. These are observed environment/tooling issues, not product performance results. The remaining Starlette TestClient deprecation warning is disclosed in results and troubleshooting.

## Responsibility boundaries

| Category | Work |
|---|---|
| Ordinary deterministic automation | CSV reading, header signature lookup, alias rules, enum/date conversion, validation, SQL uniqueness, replay, approval payload checks, registry reuse, fixture comparison and test execution |
| AI-assisted development | Codex compared synthetic schemas and failures, proposed/refined the normalization design, implemented code/UI/tests, investigated environment failures, checked screenshots and produced this evidence |
| Humans still required | Confirm vendor/business semantics, choose application year versus graduation year, authorize ignored fields/date contracts, reconcile changed decisions, review engineering changes, and decide production data/access policies |

No elapsed human engineering time, productivity multiplier, token/cost savings, or human-only team baseline was measured. The measured gain is fixture import coverage and fewer required schema interventions. AI assistance is documented as how the engineering work was carried out; it is not isolated as a causal experimental variable.
