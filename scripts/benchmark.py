"""Comparable baseline/after API runs. No wall-clock or human-time claims."""
import hashlib
import json
import os
import platform
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from backend.main import app
from scripts.scenarios import EXPECTED, approve_ambiguous, expected_records, upload


def canonical_multiset(rows):
    return Counter(tuple(sorted(row.items())) for row in rows)


def validate_canonical_rows(actual, expected, context):
    actual_counts, expected_counts = canonical_multiset(actual), canonical_multiset(expected)
    assert actual_counts == expected_counts, (
        f"{context}: missing={expected_counts - actual_counts}, unexpected={actual_counts - expected_counts}"
    )


def verify_persisted(records, expected, workflow):
    # Multiple accepted/unchanged source rows can represent one stored identity.
    unique = {}
    for row in expected:
        identity = (row["applicant_id"], row["year"])
        assert identity not in unique or unique[identity] == row, "Conflicting persistence oracle"
        unique[identity] = row
    actual = [{key: value for key, value in row.items() if key != "workflow"}
              for row in records if row["workflow"] == workflow]
    validate_canonical_rows(actual, unique.values(), f"{workflow} persisted records")


def summarize(result, truth):
    oracle = expected_records(truth)
    correct = sum((canonical_multiset(result["accepted"]) & canonical_multiset(oracle)).values())
    wrong = len(result["accepted"]) - correct
    held = result.get("held", 0)
    assert len(result["accepted"]) + result["rejected"] + held == result["total"]
    # Only the two review fixtures have held rows, and all of those rows are valid.
    assert not held or truth["invalid"] == 0
    rejected_valid = truth["valid"] - correct - held
    return {"accepted_valid": correct, "rejected_valid": rejected_valid,
            "held_valid": held, "invalid_rejected": result["rejected"] - rejected_valid,
            "incorrect_silent_mappings": wrong, "status": result["status"],
            "accepted": len(result["accepted"]), "rejected": result["rejected"],
            "mapping": result["mapping"], "schema_departure_surfaced": result["drift"]}


def main():
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "platform": platform.platform(), "fixture_sha256": {
                  name: hashlib.sha256((ROOT / "fixtures" / name).read_bytes()).hexdigest() for name in EXPECTED},
              "oracle_sha256": hashlib.sha256((ROOT / "fixtures/expected.json").read_bytes()).hexdigest(),
              "sample": {"files": len(EXPECTED), "rows": sum(t["valid"] + t["invalid"] for t in EXPECTED.values()),
                         "valid": sum(t["valid"] for t in EXPECTED.values()), "invalid": sum(t["invalid"] for t in EXPECTED.values())}, "workflows": {}}
    original_db = os.environ.get("IMPORT_DB")
    try:
        with tempfile.TemporaryDirectory(prefix="benchmark-", dir=evidence) as temporary:
            os.environ["IMPORT_DB"] = str(Path(temporary) / "run.sqlite3")
            with TestClient(app) as client:
                for workflow in ("baseline", "improved"):
                    initial = {name: upload(client, workflow, name) for name in EXPECTED}
                    corrections = sum(r["status"] in ("schema_error", "awaiting_review") for r in initial.values())
                    assert corrections == sum(t[f'manual_{"before" if workflow == "baseline" else "after"}'] for t in EXPECTED.values())
                    final = dict(initial)
                    actions = 0
                    if workflow == "improved":
                        final["ambiguous_v3.csv"] = approve_ambiguous(client, initial["ambiguous_v3.csv"]["id"])
                        actions += 1
                    expected_stored = []
                    for name, result in final.items():
                        # Explicit scenario coverage, independent of reported acceptance counts.
                        supported = name == "atlas_v1.csv" if workflow == "baseline" else name != "unknown_v1.csv"
                        oracle = expected_records(EXPECTED[name]) if supported else []
                        validate_canonical_rows(result["accepted"], oracle, f"{workflow}/{name} accepted")
                        expected_stored.extend(oracle)
                    files = {name: summarize(result, EXPECTED[name]) for name, result in final.items()}
                    before_replay = [r for r in client.get("/api/records").json() if r["workflow"] == workflow]
                    verify_persisted(before_replay, expected_stored, workflow)
                    for name in EXPECTED:
                        assert upload(client, workflow, name)["replayed"] is True
                    after_replay = [r for r in client.get("/api/records").json() if r["workflow"] == workflow]
                    verify_persisted(after_replay, expected_stored, workflow)
                    assert before_replay == after_replay
                    regression = {name: files[name]["accepted_valid"] == EXPECTED[name]["valid"] and files[name]["incorrect_silent_mappings"] == 0
                                  for name in ("atlas_v1.csv", "birch_v1.csv", "cedar_v1.csv", "atlas_v2.csv")}
                    metrics = {"accepted_valid": sum(f["accepted_valid"] for f in files.values()),
                               "rejected_valid": sum(f["rejected_valid"] for f in files.values()),
                               "held_valid": sum(f["held_valid"] for f in files.values()),
                               "invalid_rejected": sum(f["invalid_rejected"] or 0 for f in files.values()),
                               "manual_corrections_required_initially": corrections, "approvals_executed": actions,
                               "schema_departures_surfaced": sum(r["drift"] for r in initial.values()),
                               "uncertain_schemas_held_initially": sum(r["status"] == "awaiting_review" for r in initial.values()),
                               "incorrect_silent_mappings": sum(f["incorrect_silent_mappings"] for f in files.values()),
                               "records_before_replay": len(before_replay), "records_after_replay": len(after_replay),
                               "record_growth_on_replay": len(after_replay) - len(before_replay),
                               "format_regressions_passing": sum(regression.values()), "format_regressions_total": len(regression)}
                    assert metrics["incorrect_silent_mappings"] == 0
                    assert metrics["accepted_valid"] == (3 if workflow == "baseline" else 14)
                    assert metrics["invalid_rejected"] == 4
                    assert metrics["schema_departures_surfaced"] == 5
                    assert len(client.get("/api/runs").json()) == (6 if workflow == "baseline" else 12)
                    report["workflows"][workflow] = {"metrics": metrics, "files": files, "format_regressions": regression,
                                                      "initial_runs": initial, "final_runs": final}
    finally:
        if original_db is None:
            os.environ.pop("IMPORT_DB", None)
        else:
            os.environ["IMPORT_DB"] = original_db
    (evidence / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    for workflow, data in report["workflows"].items():
        print(f'{workflow}: {json.dumps(data["metrics"], sort_keys=True)}')
    print("All benchmark assertions passed. Evidence: evidence/benchmark.json")


if __name__ == "__main__":
    main()
