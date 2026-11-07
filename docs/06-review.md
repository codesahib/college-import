# Follow-up correctness and evidence audit

Session: 2026-11-06 Toronto; verification captured 2026-11-07 UTC on Windows/Chrome.
Implementation: `a63eb3be527f89e1604b7b0af64fc292cfd5c0fd`.
Starting commit: `161281a33da919d84ead675b828b6b78651ce5f3`, clean tree.
Baseline tag remains `615da24891c1bd817c5b62d4109b6082a50395c4`.

This was a fresh Codex-assisted code review and executable reproduction, not independent human review. No human-time comparison, production data, runtime AI, or productivity claim is introduced.

## One reproduced defect and correction

The shared row validator called `int(year)` before bounding its digit count. A 5,000-digit ASCII year fits the existing upload/CSV limits but exceeds Python's default integer conversion limit. Uploading that row alongside a valid row returned HTTP 422 for the entire import in both workflows, losing partial acceptance. The same data was safely quarantined under ambiguous headers, but approving its mapping raised an unhandled `ValueError` (HTTP 500). The approval transaction already rolled back; there was no demonstrated partial mapping or record write.

The regression file was written and executed before the implementation change:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_year_validation.py -q -p no:cacheprovider
```

Before: **3 failed, 10 passed**, captured in [year-validation-red.txt](../evidence/year-validation-red.txt). Two API tests observed 422 instead of a row report; the approval test raised the integer conversion exception. The passing checks include a pre-fix injected validation exception proving approval leaves the registry and records empty and the run quarantined, plus normal year boundaries and leading-zero behavior.

The correction converts at most four significant ASCII digits and preserves the existing numeric-year contract, whitespace trimming and leading-zero acceptance. Out-of-range or oversized significant values become ordinary source-column row errors. It does not change interpreter settings, widen accepted years, guess mappings, or catch arbitrary exceptions as successful approvals. Extremely long leading-zero representations of an otherwise valid year can now normalize safely instead of hitting Python's conversion limit.

After: **13 passed**, captured in [year-validation-green.txt](../evidence/year-validation-green.txt). Direct imports in both workflows persist one valid peer, reject the malformed row and replay without growth. Reviewed imports commit the mapping, one valid record and completed run together, with `application_year` identified as the bad source column. Rollback fault injection still passes. Canonical years 2000 and 2100, whitespace, ordinary leading zeroes, invalid boundaries and non-ASCII digits are checked.

This changes shared validation in the current baseline workflow too. `baseline-demo` is untouched; the current parser module is no longer byte-identical to that tag. Strict baseline header detection and all six declared fixture results remain unchanged. This is malformed-input reliability hardening, not another gain in the headline benchmark.

## Review findings within the existing contract

- Approvals require all four distinct existing source columns, explicit unused-column acknowledgement, an allowed date contract and a reviewer label. Stored content and normalized header signature are used server-side. `BEGIN IMMEDIATE` and unique constraints serialize mapping version/signature publication, upload replay and record insertion. Existing invalid-approval and concurrent-replay tests pass. No higher-priority corruption defect was reproduced within this bounded contract.
- This is one unauthenticated loopback admin workspace, not a multi-tenant service. Workflow keys isolate before/after records. Mappings are global and applicant IDs are assumed globally stable across fictional exports. Same-header/different-meaning vendors or source-local identity collisions require authenticated source namespaces/contract governance before real integration; adding tenancy is outside this audit's one-fix scope.
- Mapping approval checks structure, not business meaning. A syntactically valid bad decision can be published, reviewer text is not verified identity, and mappings have no replacement/revocation workflow. Those are existing documented limitations, not guarantees established by this patch.
- The benchmark sends identical bytes to workflow-isolated records in a fresh temporary database. It checks full canonical values against a declared synthetic oracle, executes one approval and replays all six files. Baseline 3/15 versus improved 14/15 remains unchanged; one valid unknown-schema row remains held. Schema-correction counts are required future interventions, not measured work time or executed baseline edits. Six tiny hand-authored fixtures do not establish enterprise coverage or scale.

## Complete verification and remaining limits

Executed `PLAYWRIGHT_CHANNEL=chrome` with the existing environment's `python scripts/verify.py`: **44 backend tests**, TypeScript checking, production build, benchmark assertions and **2 Chrome browser tests** all passed. Actual command exit codes and output are in [verification.json](../evidence/verification.json); JUnit and Playwright details and six refreshed screenshots are indexed in [evidence/README.md](../evidence/README.md). Evidence was generated from the source committed as the implementation hash above; later changes are documentation and artifacts only.

The initial sandbox attempt could not launch the existing Microsoft Store Python interpreter. Authorized execution outside that sandbox completed all required checks. No required repository verification was omitted. Linux/WSL, bundled Chromium, production authentication, load/fuzz testing and a human usability study were not run or claimed. Starlette's existing TestClient/httpx deprecation warning remains. No external session was stopped; no push, deployment, global dependency installation, or baseline-tag movement occurred.

Next maintenance work should address the existing TestClient dependency warning and specify authenticated source/contract identity and audited mapping replacement before using real data. It should not turn this local demonstration into an implied production system.
