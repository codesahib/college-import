# CI-002: targeted benchmark and workflow fixes

Follow-up to the read-only CI-001 review. Starting HEAD: `f2460c2a1d368924132dabcbc8f4e69be0ec45c7`. Only its two confirmed findings were addressed. Historical reports and root `evidence/` artifacts remain intact; new execution evidence is in [`evidence/ci-002/`](../evidence/ci-002/). The baseline tag remains `615da24891c1bd817c5b62d4109b6082a50395c4`.

## Benchmark oracle

Previously, every accepted dictionary that appeared anywhere in the oracle earned credit. Three copies of one expected identity could therefore replace three distinct rows without a silent-mapping penalty. Replay checks only compared stored records before and after replay.

`scripts/benchmark.py` now uses canonical multisets, caps correct-row credit by expected multiplicity, and requires exact accepted coverage for each declared scenario, independent of reported counts. It independently compares stored identity/value coverage to the expected records both before and after replay. Expected persistence collapses repeated identical source identities while refusing contradictory oracle values. The application still accepts valid duplicate source rows as unchanged records; no parser/persistence semantics changed. Partial imports compare the expected valid subset, not invalid or held rows.

New `backend/tests/test_benchmark_oracle.py` covers duplicate/missing accepted rows, duplicate substitution for distinct identities, missing/duplicated/wrong-value persisted rows, declared duplicate multiplicity, partial imports, and actual duplicate-source insert/unchanged/replay semantics. Before implementation: **10 failed, 1 passed**, exit 1. Two failures directly demonstrate the old membership overcount; the remaining failures identify missing comparison helpers. After implementation: **11 passed**, exit 0. Authentic logs: `oracle-red.txt`, `oracle-green.txt`.

## Pending workflow operation

The UI previously selected any delayed response even after the operator switched workflows. Both workflow buttons now use the existing `busy` state and remain disabled through response handling and data refresh. Switching resumes after completion; switching clears detail as before. Approval/reprocess/replay continue through the existing operation handler.

The new browser acceptance test holds a baseline request, attempts switching by invoking the button's DOM click, requires the disabled switch to ignore the attempt, releases the request, verifies baseline detail, then switches normally and verifies the old detail is cleared. This tests desired behavior, not the old scratch test that asserted the defect. Before implementation: **1 failed**, exit 1 (switch unexpectedly enabled/selected After). Full green browser suite: **3 passed**, exit 0, including the original approval/replay/registry and mobile smoke scenarios. Logs: `browser-red.txt`, `browser-green.txt`.

## Verification and isolation

Full backend suite: **55 passed**, exit 0 (previous 44 + 11 new cases). Typecheck and production build passed, exit 0. The benchmark passed all strengthened assertions, exit 0. Exact commands/cwds/exit codes are in `evidence/ci-002/commands.jsonl`; full test output and JUnit/Playwright JSON are alongside it. The initial oracle red command was run directly:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_benchmark_oracle.py -q -o cache_dir=.orchestrator/ci002-cache --basetemp=.orchestrator/ci002-red-temp
```

All other commands are recorded in the JSONL. Browser tests/build and benchmark used a repository-local scratch copy with original source/tests and only operational ports changed to **18012/15184**, plus scratch databases/output paths. Existing node_modules/venv were reused without installation. Existing services and the shared demo database were not stopped/reset. The copied benchmark's ROOT places all writes inside scratch; the new report was then copied to `evidence/ci-002/benchmark.json`. Old root reports were not overwritten. Red browser output was saved before fixes; its scratch runner subsequently hit a Windows-console Unicode-print error, after saving the child output/exit code. UTF-8 printing fixed the runner for green execution. This was a scratch tooling issue, not the browser failure reason.

## Outcomes and denominators

Dataset remains **6 files, 19 rows, 15 valid and 4 invalid**. Baseline accepts **3/15**, rejects 12 valid rows and four invalid rows. Improved accepts **14/15 after one simulated approval**, rejects four invalid rows, and holds the remaining unknown-format valid row. Before approval it accepts 12 valid rows. Initial correction events remain **5 versus 2**; supported-format criteria remain **1/4 versus 4/4**. Replay growth and incorrect silent mappings remain zero. The stronger evaluator now also checks expected persisted canonical coverage. No dataset/benchmark denominator changed; only test-suite denominators increased from 44 to 55 backend tests and 2 to 3 browser tests.

These are correctness and operational fixture metrics, not measured AI development productivity, engineering effort or support-ticket reductions. No prompts, transcripts, human-time comparison, causal AI gain, or runtime speedup was measured or invented. The synthetic data and same-header semantic limitations, missing authentication/tenancy, and unavailable mapping replacement remain unchanged and out of scope. Windows/Python/installed Chrome were exercised; Linux/WSL, load/fuzz testing and production deployment were not. Existing TestClient deprecation and Node color warnings remain.
