"""Invalid field values remain row errors across direct and reviewed imports."""
import pytest

from backend import normalizer
from backend.parser import validate
from .test_improvement import approval, client, send


@pytest.mark.parametrize("workflow", ["baseline", "improved"])
def test_oversized_numeric_year_does_not_abort_valid_rows(client, workflow):
    content = (
        "applicant_id,year,decision,decision_date\n"
        f"SYN-BAD,{'9' * 5000},admitted,2025-04-01\n"
        "SYN-GOOD,2025,admitted,2025-04-01\n"
    ).encode()
    response = client.post(f"/api/imports?workflow={workflow}", files={"file": ("large-year.csv", content)})
    assert response.status_code == 200
    result = response.json()
    assert result["inserted"] == 1
    assert result["rejected"] == 1
    assert [row["applicant_id"] for row in result["accepted"]] == ["SYN-GOOD"]
    assert [(error["row"], error["column"]) for error in result["errors"]] == [(2, "year")]
    assert len(client.get("/api/records").json()) == 1
    replay = client.post(f"/api/imports?workflow={workflow}", files={"file": ("large-year.csv", content)})
    assert replay.json()["replayed"] is True
    assert len(client.get("/api/records").json()) == 1


def test_approval_with_oversized_year_records_row_error_and_valid_peer(client):
    content = (
        "student_key,application_year,graduation_year,outcome,decision_on\n"
        f"SYN-BAD,{'9' * 5000},2029,Accepted,2025-04-01\n"
        "SYN-GOOD,2025,2029,Accepted,2025-04-01\n"
    ).encode()
    run = send(client, "large-year-review.csv", content).json()
    assert run["status"] == "awaiting_review"
    response = client.post(f'/api/runs/{run["id"]}/approve', json=approval())
    assert response.status_code == 200
    result = response.json()
    assert result["inserted"] == 1
    assert result["rejected"] == 1
    assert [row["applicant_id"] for row in result["accepted"]] == ["SYN-GOOD"]
    assert [(error["row"], error["column"]) for error in result["errors"]] == [(2, "application_year")]
    assert len(client.get("/api/records").json()) == 1
    assert len(client.get("/api/mappings").json()["approvals"]) == 1
    assert client.get("/api/runs").json()[0]["status"] == "completed"


def test_approval_rolls_back_when_row_validation_raises(client, monkeypatch):
    run = send(client, "ambiguous_v3.csv").json()

    def fail_validation(_values):
        raise ValueError("Injected validation failure")

    monkeypatch.setattr(normalizer, "validate", fail_validation)
    with pytest.raises(ValueError, match="Injected validation failure"):
        client.post(f'/api/runs/{run["id"]}/approve', json=approval())
    assert client.get("/api/records").json() == []
    assert client.get("/api/mappings").json()["approvals"] == []
    assert client.get("/api/runs").json()[0]["status"] == "awaiting_review"


@pytest.mark.parametrize("text,expected", [
    ("2000", 2000), ("2100", 2100), (" 2025 ", 2025), ("02025", 2025),
    ("1999", None), ("2101", None), ("２０２５", None), ("2e3", None), ("", None),
])
def test_year_contract_is_preserved(text, expected):
    record, errors = validate({"applicant_id": "SYN-YEAR", "year": text,
                               "decision": "admitted", "decision_date": "2025-04-01"})
    assert record["year"] == expected
    assert bool(errors) == (expected is None)
