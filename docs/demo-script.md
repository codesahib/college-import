# Presenter script: admissions CSV maintenance

Allow about five minutes as a presentation outline; this is not a measured engineering-time claim. Audience: a hiring manager or small engineering team. Describe this as an independent synthetic demonstration, never a Beacon deployment.

## Prepare

Follow README setup, stop existing servers, and run from the repository root:

```bash
source .venv/bin/activate
./scripts/reset-demo.sh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
```

In another terminal run `npm --prefix frontend run dev`. Open http://127.0.0.1:5174. Seed state: 6 runs per workflow, 3 baseline records, 12 improved records, and 2 improved review queues. Seed does not approve the ambiguous file.

## 1. Start with the operational problem

“An admissions admin uploads historical vendor exports. Support and engineering maintain a strict CSV contract. When a vendor changes its export, valid rows stop arriving.”

Select **Before · strict parser**, then open `atlas_v1.csv` from history. Show its 3 accepted rows and one invalid year at row 5. Open `atlas_v2.csv`. It has four renamed/reordered columns and changed decision spellings; all four rows are rejected at the header boundary. Three of those rows are valid according to the synthetic fixture oracle.

Show `fixtures/atlas_v1.csv` beside `fixtures/atlas_v2.csv` and `backend/parser.py`. The CSV parser itself is sound; one strict contract limits coverage. Birch and Cedar history show the same support-level symptom.

## 2. Show the engineering intervention and resulting workflow

Select **After · safer mappings**, open `atlas_v2.csv`, and point to `Aliases@1` and **Drift detected**. Three rows normalize successfully. The missing ID is explained at row 5, source column `student_key`, with a concrete requirement. Accepted rows show canonical decision spellings and ISO dates. Download the JSON report.

Open Birch and Cedar to show exact configured date formats and source-column validation, then show `backend/mappings.json`. Explain: “Codex helped investigate and implement this. The running importer uses CSV parsing, declarative rules and database constraints. It makes no LLM requests.”

## 3. Demonstrate the safety boundary

Open `ambiguous_v3.csv`. The run has 2 held rows, zero accepted/rejected rows and no records written. Source preview shows `application_year=2025` and `graduation_year=2029`; the application-year dropdown is unresolved.

Choose `application_year`. Keep the ISO date format. Mapping name defaults to `Atlas review`, reviewer to `Demo operator`; these are demo labels. Read the explicit ignored-column acknowledgement for `graduation_year`, check it and click **Approve mapping & import**. The run becomes processed with 2 accepted/inserted rows. Improved stored records increase **12 → 14**. Accepted application years are 2025.

“A person supplies business meaning. Approval records a reusable schema configuration and validates every row. It is not permission to bypass row checks.”

## 4. Replay and inspect the handoff

Select `ambiguous_v3.csv` in the synthetic fixture selector and click **Import sample**. The replay message returns the same run; records stay at 14. Select **Mapping registry**. Show the named version, application-year choice, ignored graduation column, and approval log. A later file with the same header signature reuses this configuration automatically; exact reupload returns the historical run.

Return to imports and open `unknown_v1.csv`. It remains held, with missing ID/date header explanations. Leave it unresolved: there is no claim that automation knows a new vendor's business contract.

## 5. Show verified evidence

Stop demo servers before browser verification. From the active venv:

```bash
python scripts/verify.py
```

If using installed Chrome, prefix with `PLAYWRIGHT_CHANNEL=chrome`. The benchmark has its own isolated database and approves one synthetic mapping; it does not alter the demo database. Show `docs/03-results.md` and `evidence/benchmark.json`:

- 6 files, 19 rows, 15 valid and 4 invalid.
- Valid imports 3 → 14; required schema-correction events 5 → 2. One approval was executed, one schema remains unresolved.
- Invalid rows rejected 4/4 both; visible departures 5/5 both; zero silent mismatches and zero replay record growth both.
- Four supported-format criteria 1/4 → 4/4. All 31 backend tests and both browser smoke tests pass; typecheck/build pass.

Close with the maintenance path: add a synthetic changed-format fixture, confirm semantic contract, adjust declarative rules, add canonical-value/error regressions, run verification and review the evidence. Do not claim measured engineering time savings or production reliability from these tiny fixtures.

## If a demonstration state differs

Already approved? Stop servers and reset, then restart. Counts aggregate live imports, not a fixed slide. If a replay shows the original inserted count, explain that it is the historical run and point to the replay notice and unchanged stored-record count. If approval says 409 because another run approved the signature, use **Retry with approved mappings** on the held run. Do not overwrite historical records to force a presentation outcome.
