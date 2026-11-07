"""Reset only a SQLite file inside this repository. Stop servers first."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="backend/demo.sqlite3")
    parser.add_argument("--empty", action="store_true")
    args = parser.parse_args()
    target = (ROOT / args.database).resolve()
    if not target.is_relative_to(ROOT) or target.suffix != ".sqlite3":
        parser.error("Database must be a .sqlite3 file inside this repository.")
    for suffix in ("", "-wal", "-shm", "-journal"):
        file = Path(str(target) + suffix)
        if file.exists():
            file.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    os.environ["IMPORT_DB"] = str(target)
    from backend.db import connect
    connection = connect()
    connection.close()
    if not args.empty:
        from fastapi.testclient import TestClient
        from backend.main import app
        from scripts.scenarios import EXPECTED, upload
        with TestClient(app) as client:
            for workflow in ("baseline", "improved"):
                for filename in EXPECTED:
                    upload(client, workflow, filename)
            print(f"Seeded {len(client.get('/api/runs').json())} runs and {len(client.get('/api/records').json())} records.")
            print("Improved: 12 records; 2 quarantined schemas await review. Baseline: 3 records.")
    print(f"Database: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
