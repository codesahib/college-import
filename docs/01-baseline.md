# Baseline gate

Independent synthetic demonstration of maintaining an admissions CSV ingestion service.

The existing operational process is: support receives a CSV, an admin uploads it, a strict parser validates one documented contract, and the UI shows accepted/rejected rows and prior runs. Engineering must update the parser when vendor contracts change. There is no runtime AI.

`backend/parser.py:parse_baseline` uses Python's CSV reader, accepts column reordering, checks four canonical headers, validates IDs, years, decision enums and ISO dates, and reports row/column errors. This is a reasonable single-vendor first implementation, not deliberately corrupted logic. `backend/main.py` persists runs and accepted records in SQLite. Identical file uploads reuse a run; record identity is workflow + applicant ID + application year. Existing records are preserved on duplicate identity. The improvement will refine conflict reporting.

Fixtures: `atlas_v1.csv` has three valid rows and one out-of-range year; `atlas_v2.csv` contains three valid changed-format rows and one missing ID. Strict-v1 rejects the entire changed schema before inspecting rows. The baseline supports the original contract only; it makes no claim to support other vendors.

Gate: run `python -m pytest backend/tests/test_baseline.py`, then `cd frontend && npm run build`. Run the backend with `python -m uvicorn backend.main:app --port 8002` and frontend with `npm run dev`. Upload the two fixtures and inspect history. Commit as `baseline: working original workflow` and tag `baseline-demo` before changing the parser.
