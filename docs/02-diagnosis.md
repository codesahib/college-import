# Diagnosis gate

Run `python scripts/diagnose.py`; the captured output is `evidence/baseline-diagnosis.json`. All fixtures are fictional. `fixtures/expected.json` is the declared truth: 19 rows, 15 valid and 4 invalid, across six files.

Observed baseline: only Atlas v1 is accepted (3 valid rows). Five header signatures fail at row 1, rejecting 12 other valid rows alongside three invalid rows. Baseline basic validation works as designed; the failure is a contract coverage gap. `backend/tests/test_baseline.py` explicitly tests that shortcoming as expected behavior, rather than falsely asserting that the baseline supports changed schemas.

Support reproduction: upload `fixtures/atlas_v2.csv`. The report expects `applicant_id,year,decision,decision_date`, but receives `outcome,decision_on,student_key,cycle`. Compare the sample values with Atlas v1: headers are renamed/reordered and enum spellings differ. The baseline correctly refuses an unsupported contract, but provides only one generic header message. Birch has month/day/year dates; Cedar has day.month.year dates. Those require explicit format contracts, not a date heuristic. `ambiguous_v3.csv` contains both application and graduation years; silently choosing either would be unsafe. `unknown_v1.csv` contains two deliberately unrecognized names.

Suspected cause, confirmed by reading `parse_baseline`: one header-set check and one enum/date vocabulary couple vendor recognition to row validation. There is no versioned mapping registry or operator review path. Repeated parser edits increase regression exposure.

Targets (not measured outcomes): support the four unambiguous formats without code changes per upload; quarantine ambiguous/unknown schemas; accept 14 of the 15 valid rows after one reviewed mapping approval, leaving the unknown file held; reject all four invalid rows; zero incorrect canonical records; replay all six files without record growth. Recognize all five noncanonical schemas visibly. Reduce required schema correction events from 5 to 2. Held rows are tracked separately from rejected rows.

Correction-count definition: one distinct unsupported schema requiring either an engineering mapper change (baseline) or a submitted mapping-configuration approval (improved) is one required correction event, irrespective of clicks/fields/time. The benchmark counts initial requirements; it actually executes one improved approval for the ambiguous fixture. The unknown fixture remains unresolved. Baseline corrections are required events inferred from parser output, not performed code edits or human time measurements.

Proposed smallest intervention: a declarative versioned mapping registry, conservative unique aliases, exact signatures, deterministic normalization, field-level validation, a quarantine approval UI, and database uniqueness with explicit conflict reporting. Keep the baseline executable and its tests unchanged for comparison.
