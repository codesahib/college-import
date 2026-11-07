# Shared project requirements (applies to all three demos)

## Objective
You are implementing a technical interview case study for a software engineer who joins acquired SaaS companies, learns unfamiliar code, introduces existing AI-assisted engineering workflows, improves engineering productivity and reliability, and leaves maintainable systems behind. This is **not** a request to add a customer-facing chatbot, to build a generic LLM wrapper, or to pretend AI is necessary where deterministic software is better.

Build a self-contained full-stack demo and document **(a) product/process without AI, (b) bottleneck, (c) AI-supported engineering process, (d) improved process/product, (e) measured outcome**.

## Strict scope
- Work inside this repo only. Do not edit sibling repositories or the user's existing portfolio website.
- Use **React + TypeScript + Vite** frontend, **FastAPI + Python** backend, SQLite for local persistence, pytest for backend tests, and Playwright for an essential UI smoke test if feasible. Prefer simple architectures over Docker/microservice overhead.
- Do not require paid APIs, hosted AI services, credentials, or access to Beacon systems. Synthetic data only. No real customer names, emails, payment details, or protected information.
- Use existing AI coding tools (Codex itself) for analysis, feature development, bug investigation, and tests. Do **not** add AI in the runtime product unless it solves a clearly explained, indispensable workflow problem; approval is not needed for routine deterministic automation.
- Use a clean UI that visibly demonstrates the before/after workflow, not just a landing page.
- All commands documented for Ubuntu/WSL. Isolate local ports per task. Include `scripts/reset-demo.sh` and a deterministic seed dataset.
- Keep scope realistic for one repository. Focus on a narrow, fully working vertical slice instead of extensive placeholder features or architecture diagrams without code.

## Mandatory phase gates
1. **Baseline.** Implement a working, intentionally limited (but realistic) existing workflow. Document the limitation in `docs/01-baseline.md`. Commit it with message `baseline: working original workflow` and make Git tag `baseline-demo`. Avoid artificially sabotaging production logic just to manufacture dramatic results.
2. **Diagnosis.** Generate reproducible scenarios that expose the bottleneck. Write `docs/02-diagnosis.md` with observed behavior, suspected causes, and measurable target. Tests should distinguish expected behavior from known shortcomings.
3. **Improvement.** Use Codex-assisted code exploration, implementation and testing to add the smallest effective improvement. Prefer deterministic logic, existing libraries, database constraints, and tests. Commit with `improvement: ...`.
4. **Evaluation.** Run reproducible baseline/after tests or scripts against comparable synthetic data. Report exact metrics in `docs/03-results.md`, including methodology, sample sizes, limitations, and outcomes that did **not** improve. Never invent timings or report suggested targets as measured results.
5. **Handoff.** Produce `README.md`, `docs/04-ai-engineering-process.md`, `docs/05-tradeoffs.md`, `docs/demo-script.md`, and `portfolio/case-study.md`. Include links or paths to code/tests and a quickstart. Document changes and handoff guidance an existing small engineering team could follow.

## What the AI documentation must contain
- What Codex examined (file paths, schemas, logs/tests).
- What decisions it proposed and what was accepted/rejected after engineering review.
- Specific changes to code, tests, and operational workflow.
- Which parts of the final workflow are **ordinary deterministic automation**, which parts benefited from **AI-assisted development**, and which parts still require humans.
- Avoid invented accounts of elapsed human engineering time or fabricated comparisons to a human-only team. If it wasn't measured, say so.

## Quality bar
- Run backend tests and frontend typecheck/build. Run the UI smoke test when tooling permits; document any unavailable browser dependencies.
- Do not leave endpoints as TODOs or dashboards with fake metrics. If a metric is displayed, derive it from live seeded data or mark it clearly as an illustrative scenario.
- Include input validation, meaningful error messages, idempotency where relevant, a deterministic reset path, and at least one negative/edge-case test.
- README must include exact setup, install, test, seed/reset, run, demo, and troubleshooting commands.
- At end, summarize features built, commands actually executed, passing/failing tests, benchmark outputs, relevant Git commits, and known limitations. Never claim to have run a command that was not run.

## Reporting to the hiring manager
Lead with the existing operational/engineering process, not AI. Show why the specific improvement matters, the before/after workflow, and verified evidence. Present the work as **independent, synthetic, portfolio-company-inspired demonstrations**, never as Beacon production changes.

# PROJECT 2 — Admissions CSV Import Maintenance Lab

## Story (not a claim about a real company)
Inspired by admissions-planning software that imports historical data exported from school systems. Engineers and support teams have to maintain parsers as upstream vendors change CSV headers/formats. The goal is to show AI-assisted issue investigation and maintenance of a deterministic ingestion pipeline, not an AI-powered counselor chatbot.

## Product WITHOUT AI / baseline workflow
- Admin uploads a synthetic college-admissions CSV with applicant/year/decision fields (no real student data).
- Existing parser supports one known format and enforces basic validation.
- UI displays accepted rows, rejected rows and historical import runs.
- Another vendor changes a field name, column order, enum spelling or date format: importer rejects or misclassifies rows. Support examines the file, recreates the error and engineering updates the mapper.

## Concrete problem to demonstrate
1. Upstream CSV schemas drift and cause repeated support tickets.
2. Rejected rows can be hard to diagnose without precise column-level explanations.
3. A quick fix for one vendor can break another, creating regression risks.
4. Engineers repeatedly read sample CSVs, parser code and error output to discover the same kinds of issues.

## AI-assisted engineering intervention
Use Codex to inspect sample failed imports, identify differences across supported schemas, propose a schema normalization approach, modify parser code and generate regression tests. Document what Codex proposed, what was reviewed, and why runtime data validation is deterministic. **Do not call an LLM for every imported row.**

## Improved workflow to implement
- Configurable, versioned vendor mappings, defensible header aliases, explicit format detection, robust row-level validation and actionable error reports.
- Quarantine/review of ambiguous mappings rather than silent guesses; operator can approve a proposed mapping configuration via admin UI.
- Import-history dashboard with run status, row counts, errors, schema-drift indicators and mapping versions.
- An automated regression fixture suite for at least three fictional vendor CSV formats and a newly changed format.
- Safe idempotency: reuploading a file doesn't duplicate records; document identity and merge rules.

## Required demonstration scenario
- Seed CSV v1, a second vendor format, and an unexpected schema-change CSV.
- Show baseline fail on changed format and a support-level diagnosis.
- Show improved import with recognized aliases, precise errors and approval for ambiguous fields.
- Replay valid imports, verify row counts and that no records duplicate.
- Include a reset-and-seed command.

## Real measurements
Benchmark/test, using identical fixtures, at least:
- Accepted and rejected valid rows by file format.
- Number of manual mapping corrections required (count defined operator actions, not invented minutes).
- Count of correctly surfaced schema errors and incorrect silent mappings (target 0; report actual).
- Parser regression test results across each format.

## Tech / local ports
React + TypeScript + Vite frontend `5174`, FastAPI backend `8002`, SQLite. Make vendor fixtures and parser logic easy to inspect. Use CSV standard libraries or established parsers, not ad hoc brittle string splitting.

## Deliberately out of scope
Real schools, real student PII, actual college admissions predictions, vendor credentials or APIs, dynamically generated executable parser code, runtime LLM interpretation of private student records.

## Case-study headline
"Modernizing a Fragile Import Pipeline with AI-Assisted Diagnosis, Safer Mappings and Regression Testing"
