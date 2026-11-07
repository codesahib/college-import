# Tradeoffs and small-team handoff

## Why this architecture

A single FastAPI process and SQLite make a local admin workflow inspectable without infrastructure. React + TypeScript + Vite provide a real upload/review dashboard on 5174; FastAPI serves the API on 8002. JSON mappings are reviewable data rather than dynamically executed parser code. The standard-library CSV reader handles quoted delimiters, BOM and multiline records. No runtime AI or external calls are needed.

The stored workflow key isolates before/after records inside one database so the same fixture can be compared safely. SHA-256 file identity avoids duplicate runs; composite record keys prevent record duplication across files with different byte representations. `BEGIN IMMEDIATE` serializes write decisions; a unique upload index and record primary key enforce identity below application code. Small imports are processed synchronously and accepted rows commit together with the run. Invalid rows are reported while valid rows can commit: this is partial acceptance by design, not file-level all-or-nothing validation.

## Conservative detection and its limits

Header normalization trims, lowercases and collapses whitespace into underscores; it does not fuzzy-match text. Duplicate normalized names fail. Exact supported or approved signatures win before unique complete aliases. Automatic aliases require a complete four-column ISO-date contract. Extra columns are held even when they look harmless, so ignoring a column is an explicit operator decision. Graduation year is a review-only candidate.

This favors visible interruptions over guessing. It will quarantine some safe files and reject unsupported date/enum vocabularies. The three date formats are vendor contracts, not date inference. Same headers with different semantics across vendors are out of scope: an authenticated vendor/contract identifier would be needed to distinguish those safely. Drift flags mean noncanonical header departures, including recognized vendors; they are not historical anomaly detection.

Mappings carry name/version/source and their exact configuration is snapshotted in each completed run. Operator approvals create an immutable signature contract and increasing version for that name. A second approval for the same signature returns 409; another quarantined run can reprocess with the approved mapping. There is no editing, revocation, rollback UI, or automatic migration of old successful imports. For this demo, correct a bad approval by resetting and seeding. A real team would add an audited replacement workflow and explicit reprocessing policy before operational use.

## Identity and data policies

Applicant IDs are synthetic, globally stable across fictional sources, case-sensitive and trimmed. The `(workflow, applicant_id, year)` identity is not an inferred person match. If real sources use local IDs, add a source namespace or verified crosswalk before integrating them. Different decisions or dates for an existing identity are conflicts, not automatic updates. Manual business reconciliation remains necessary. Exact file replay returns historical inserted counts and a replay marker; it never inserts those counts again.

Raw synthetic files and full JSON reports are retained in SQLite until reset. There is no retention scheduler, encryption, authentication, verified reviewer identity, audit tamper protection, pagination or external integration. Bind to loopback. Frontend errors escape through React; SQL uses parameterized values. Reports download JSON rather than executing spreadsheet formulas. Two-MB parser read and 10,000-row limits keep the demo bounded, but they do not impose a pre-multipart network ingress limit. Add a body limit at the server/proxy before exposure.

## Maintain a new vendor contract

1. Reproduce with a minimal **synthetic** fixture under `fixtures/`. Capture expected valid rows, invalid rows, dates and error columns. Keep previous fixture versions.
2. Determine field meanings from the vendor contract. Do not infer application year, person identity or locale from plausible-looking values alone.
3. For a new exact known format, add a declarative mapping to `backend/mappings.json` with a meaningful version/date format. For general aliases, require a clear shared meaning and test ambiguity/extra columns. Enum aliases are shared and must have the same decision meaning across all supported formats.
4. Add a parameterized regression in `backend/tests/test_improvement.py` checking canonical dictionaries and source-column errors, not just accepted counts. Add negative/conflict cases when changing semantics. If the benchmark dataset changes, update `fixtures/expected.json`, the oracle generation in `scripts/scenarios.py` if necessary, and the documented sample/methodology together.
5. Run `python scripts/verify.py` with demo servers stopped. Review raw evidence and desktop/mobile screenshots. Seed a fresh demo and rehearse `docs/demo-script.md`. Review the diff and mapping policy before shipping.

Support can download a run report and provide run ID, mapping version, schema signature/source columns, exact synthetic reproduction, and error rows. Engineering owns field semantics, tests and releases. Operators can approve new signatures through the UI, but approval is not proof the underlying semantics are correct.

## Existing local database / dependency handoff

The schema uses `CREATE TABLE/INDEX IF NOT EXISTS`; it is not a migration system. The baseline-to-improved changes add a unique run index and mapping table; the seeded baseline already has unique files, so this is compatible. An independently modified database with duplicate workflow/digests needs manual reconciliation before adding that index. Use the reset script for repeatable demo state, after stopping servers. Keep a copy of a useful synthetic database inside the repo if inspecting it; do not treat a demo reset as a production migration.

Direct Python dependencies are pinned in `backend/requirements.txt`; npm transitive versions are captured in `frontend/package-lock.json` and installed with `npm ci`. Python transitives are not fully locked. TestClient currently emits a Starlette deprecation warning for `httpx`, which should be addressed in the next dependency-maintenance pass with regression validation. Runtime/OS differences can affect browser startup; the captured result is Windows/Chrome, not a claim of tested Linux support. No performance-at-scale or production-readiness claim is made.
