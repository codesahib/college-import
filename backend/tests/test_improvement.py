import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.normalizer import initial_mappings, parse_improved
from .test_baseline import FIXTURES


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPORT_DB", str(tmp_path / "test.sqlite3"))
    return TestClient(app)


def send(client, filename, content=None):
    return client.post("/api/imports?workflow=improved", files={"file": (filename, content if content is not None else (FIXTURES / filename).read_bytes())})


def approval():
    return {"name": "Atlas reviewed", "reviewer": "Synthetic operator", "date_format": "%Y-%m-%d",
            "fields": {"applicant_id": "student_key", "year": "application_year", "decision": "outcome", "decision_date": "decision_on"},
            "ignored": ["graduation_year"]}


@pytest.mark.parametrize("filename,version,bad_column", [
    ("atlas_v1.csv", "Atlas@1", "year"), ("birch_v1.csv", "Birch@1", "decision_date"),
    ("cedar_v1.csv", "Cedar@1", "verdict"), ("atlas_v2.csv", "Aliases@1", "student_key")])
def test_vendor_regression(filename, version, bad_column):
    result = parse_improved((FIXTURES / filename).read_bytes(), initial_mappings())
    assert result["status"] == "completed"
    assert len(result["accepted"]) == 3
    assert result["rejected"] == 1
    assert result["mapping"] == version
    assert [row["decision"] for row in result["accepted"]] == ["admitted", "denied", "waitlisted"]
    assert [row["decision_date"] for row in result["accepted"]] == [f'{row["year"]}-04-0{i}' for i, row in enumerate(result["accepted"], 1)]
    assert result["errors"][0]["column"] == bad_column
    assert result["errors"][0]["row"] == 5


@pytest.mark.parametrize("filename", ["ambiguous_v3.csv", "unknown_v1.csv"])
def test_unknown_or_ambiguous_schema_never_guesses(client, filename):
    result = send(client, filename).json()
    assert result["status"] == "awaiting_review"
    assert result["accepted"] == []
    assert result["held"] > 0
    assert result["rejected"] == 0
    assert client.get("/api/records").json() == []
    if filename == "ambiguous_v3.csv":
        assert result["proposal"]["fields"]["year"] == ""
        assert result["proposal"]["candidates"]["year"] == ["application_year", "graduation_year"]


def test_review_approval_reuse_and_audit(client):
    first = send(client, "ambiguous_v3.csv").json()
    response = client.post(f'/api/runs/{first["id"]}/approve', json=approval())
    assert response.status_code == 200
    result = response.json()
    assert result["inserted"] == 2
    assert result["mapping"] == "Atlas reviewed@1"
    assert {r["year"] for r in result["accepted"]} == {2025}
    assert client.post(f'/api/runs/{first["id"]}/approve', json=approval()).status_code == 409
    replay = send(client, "renamed.csv", (FIXTURES / "ambiguous_v3.csv").read_bytes()).json()
    assert replay["replayed"] is True
    changed = (FIXTURES / "ambiguous_v3.csv").read_bytes().replace(b"SYN-E01", b"SYN-E03")
    reused = send(client, "new-batch.csv", changed).json()
    assert reused["status"] == "completed"
    assert reused["inserted"] == 1 and reused["unchanged"] == 1
    assert len(client.get("/api/records").json()) == 3
    assert client.get("/api/mappings").json()["approvals"][0]["reviewer"] == "Synthetic operator"


@pytest.mark.parametrize("mutation", [
    {"ignored": []}, {"fields": {"applicant_id": "student_key"}},
    {"date_format": "%d/%m/%Y"}, {"reviewer": " "},
    {"fields": {"applicant_id": "student_key", "year": "student_key", "decision": "outcome", "decision_date": "decision_on"}},
    {"fields": {"applicant_id": "student_key", "year": "absent", "decision": "outcome", "decision_date": "decision_on"}},
])
def test_invalid_approval_is_atomic(client, mutation):
    run = send(client, "ambiguous_v3.csv").json()
    response = client.post(f'/api/runs/{run["id"]}/approve', json={**approval(), **mutation})
    assert response.status_code == 422
    assert client.get("/api/records").json() == []
    assert client.get("/api/mappings").json()["approvals"] == []
    assert client.get("/api/runs").json()[0]["status"] == "awaiting_review"


def test_conflicts_are_rejected_not_overwritten(client):
    send(client, "atlas_v1.csv")
    changed = (FIXTURES / "atlas_v1.csv").read_bytes().replace(b"SYN-A01,2024,admitted", b"SYN-A01,2024,denied")
    result = send(client, "correction.csv", changed).json()
    assert result["inserted"] == 0
    assert result["unchanged"] == 2
    assert result["rejected"] == 2
    assert result["errors"][-1]["row"] == 2
    assert "Identity conflict" in result["errors"][-1]["message"]
    assert client.get("/api/records").json()[0]["decision"] == "admitted"


def test_concurrent_replay_is_unique(client):
    client.get("/api/health")
    # Initialize tables before dispatch; both inserts still race on the same digest.
    client.get("/api/records")
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: send(client, "atlas_v1.csv"), range(2)))
    assert all(response.status_code == 200 for response in responses)
    assert len(client.get("/api/runs").json()) == 1
    assert len(client.get("/api/records").json()) == 3
    assert sum(bool(r.json().get("replayed")) for r in responses) == 1


@pytest.mark.parametrize("content,status", [
    (b"", 422), (b"\xff\xfe", 422), (b'a,b\n"unterminated', 422),
    (b"x" * 2_000_001, 413),
    (b"applicant_id,year,decision,decision_date\n" + b"x,2024,admitted,2024-01-01\n" * 10001, 422),
])
def test_bad_input(client, content, status):
    assert send(client, "bad.csv", content).status_code == status
    assert client.get("/api/runs").json() == []


@pytest.mark.parametrize("header", ["applicant_id,year,decision,decision_date,year", "applicant_id,year,decision,decision_date, YEAR ", "applicant_id,,decision,decision_date"])
def test_duplicate_or_blank_headers(header):
    result = parse_improved((header + "\nx,2024,admitted,2024-04-01,2025").encode(), initial_mappings())
    assert result["status"] == "schema_error"
    assert result["accepted"] == []


def test_bom_case_reorder_and_quoted_csv():
    content = '\ufeff DECISION ,Decision_Date,Year,Applicant_ID\naccepted,2024-04-01,2024,"SYN,QUOTED"\n'
    result = parse_improved(content.encode(), initial_mappings())
    assert result["accepted"][0]["applicant_id"] == "SYN,QUOTED"
    assert result["mapping"] == "Atlas@1"


def test_ragged_row_and_wrong_date_format():
    content = b"applicant_id,year,decision,decision_date\nx,2024,admitted\ny,2024,denied,04/01/2024\n"
    result = parse_improved(content, initial_mappings())
    assert result["rejected"] == 2
    assert result["errors"][1]["column"] == "decision_date"
    assert "%Y-%m-%d" in result["errors"][1]["message"]


def test_graduation_year_is_never_an_automatic_application_year():
    result = parse_improved(b"student_key,graduation_year,outcome,decision_on\nx,2029,Accepted,2025-04-01", initial_mappings())
    assert result["status"] == "awaiting_review"
    assert result["accepted"] == []


def test_reprocess_uses_mapping_approved_on_another_run(client):
    first = send(client, "ambiguous_v3.csv").json()
    second = send(client, "second.csv", (FIXTURES / "ambiguous_v3.csv").read_bytes() + b"\n").json()
    client.post(f'/api/runs/{first["id"]}/approve', json=approval())
    assert client.post(f'/api/runs/{second["id"]}/approve', json=approval()).status_code == 409
    result = client.post(f'/api/runs/{second["id"]}/reprocess').json()
    assert result["unchanged"] == 2 and result["inserted"] == 0
    assert result["rejected"] == 1  # Extra blank CSV record is explicitly invalid.


def test_api_validation_and_missing_runs(client):
    assert client.post("/api/imports?workflow=other", files={"file": ("a", b"a")}).status_code == 422
    assert client.post("/api/runs/999/approve", json=approval()).status_code == 404
    assert client.post("/api/runs/999/reprocess").status_code == 404
    run = send(client, "atlas_v1.csv").json()
    assert client.post(f'/api/runs/{run["id"]}/reprocess').status_code == 409
    assert client.get("/api/fixtures/missing.csv").status_code == 404
