import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "demo.sqlite3"


def connect():
    connection = sqlite3.connect(os.environ.get("IMPORT_DB", str(DEFAULT_DB)))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS records (
            workflow TEXT NOT NULL, applicant_id TEXT NOT NULL, year INTEGER NOT NULL,
            decision TEXT NOT NULL, decision_date TEXT NOT NULL,
            PRIMARY KEY(workflow, applicant_id, year));
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY, filename TEXT NOT NULL, workflow TEXT NOT NULL,
            digest TEXT NOT NULL, content BLOB NOT NULL, result TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')));
    """)
    return connection


def save_result(connection, run_id, result):
    connection.execute("UPDATE runs SET result=? WHERE id=?", (json.dumps(result), run_id))


def public_run(row):
    return {"id": row["id"], "filename": row["filename"], "workflow": row["workflow"],
            "created_at": row["created_at"], **json.loads(row["result"])}
