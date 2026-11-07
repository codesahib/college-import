"""Shared synthetic scenario actions, also exercised through the public API."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / "fixtures/expected.json").read_text())


def upload(client, workflow, filename):
    response = client.post(f"/api/imports?workflow={workflow}", files={"file": (filename, (ROOT / "fixtures" / filename).read_bytes(), "text/csv")})
    response.raise_for_status()
    return response.json()


def approve_ambiguous(client, run_id):
    response = client.post(f"/api/runs/{run_id}/approve", json={
        "name": "Atlas reviewed", "reviewer": "Benchmark operator", "date_format": "%Y-%m-%d",
        "fields": {"applicant_id": "student_key", "year": "application_year", "decision": "outcome", "decision_date": "decision_on"},
        "ignored": ["graduation_year"]})
    response.raise_for_status()
    return response.json()


def expected_records(truth):
    return [{"applicant_id": f'SYN-{truth["prefix"]}{i:02}', "year": truth["year"],
             "decision": ["admitted", "denied", "waitlisted"][i - 1], "decision_date": f'{truth["year"]}-04-{i:02}'}
            for i in range(1, truth["valid"] + 1)]
