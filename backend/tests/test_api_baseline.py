from fastapi.testclient import TestClient
from backend.main import app
from .test_baseline import FIXTURES


def test_upload_history_and_replay(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPORT_DB", str(tmp_path / "test.sqlite3"))
    client = TestClient(app)
    content = (FIXTURES / "atlas_v1.csv").read_bytes()
    response = client.post("/api/imports", files={"file": ("atlas.csv", content, "text/csv")})
    assert response.status_code == 200
    assert response.json()["inserted"] == 3
    replay = client.post("/api/imports", files={"file": ("atlas.csv", content)})
    assert replay.json()["replayed"] is True
    assert len(client.get("/api/records").json()) == 3
    assert len(client.get("/api/runs").json()) == 1
