"""Local administrative API. Bind to loopback; no production authentication."""
import hashlib
import json
from contextlib import closing
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import connect, get_mappings, public_run, save_result
from .normalizer import parse_improved, signature
from .parser import FIELDS, parse_baseline

app = FastAPI(title="Admissions Import Maintenance Lab")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@app.get("/api/fixtures")
def fixtures():
    return sorted(path.name for path in FIXTURE_DIR.glob("*.csv"))


@app.get("/api/fixtures/{name}")
def fixture(name: str):
    from fastapi.responses import Response
    if name not in fixtures():
        raise HTTPException(404, "Synthetic fixture not found.")
    return Response((FIXTURE_DIR / name).read_bytes(), media_type="text/csv")


@app.get("/api/runs")
def runs():
    with closing(connect()) as connection:
        return [public_run(row) for row in connection.execute("SELECT * FROM runs ORDER BY id DESC")]


@app.get("/api/records")
def records():
    with closing(connect()) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM records ORDER BY workflow, applicant_id, year")]


@app.get("/api/mappings")
def mappings():
    with closing(connect()) as connection:
        return {"available": get_mappings(connection),
                "approvals": [{key: row[key] for key in ("id", "name", "version", "reviewer", "created_at")}
                              for row in connection.execute("SELECT * FROM mappings ORDER BY id")]}


def persist_records(connection, workflow, result):
    inserted = unchanged = 0
    accepted, numbers = [], []
    source_rows = result.get("accepted_rows", [0] * len(result["accepted"]))
    for record, number in zip(result["accepted"], source_rows):
        existing = connection.execute("SELECT decision,decision_date FROM records WHERE workflow=? AND applicant_id=? AND year=?",
                                      (workflow, record["applicant_id"], record["year"])).fetchone()
        if existing and workflow == "improved" and (existing["decision"], existing["decision_date"]) != (record["decision"], record["decision_date"]):
            result["rejected"] += 1
            result["errors"].append({"row": number, "column": "applicant_id/year", "value": f'{record["applicant_id"]}/{record["year"]}',
                                     "message": "Identity conflict: stored decision/date differ. Existing record preserved; reconcile source data."})
            continue
        if existing:
            unchanged += 1
        else:
            connection.execute("INSERT INTO records VALUES (?,?,?,?,?)", (workflow, record["applicant_id"], record["year"], record["decision"], record["decision_date"]))
            inserted += 1
        accepted.append(record)
        numbers.append(number)
    result.update(accepted=accepted, inserted=inserted, unchanged=unchanged)
    if "accepted_rows" in result:
        result["accepted_rows"] = numbers


@app.post("/api/imports")
async def upload(file: UploadFile = File(...), workflow: Literal["baseline", "improved"] = "baseline"):
    content = await file.read(2_000_001)
    if len(content) > 2_000_000:
        raise HTTPException(413, "Maximum file size is 2 MB.")
    digest = hashlib.sha256(content).hexdigest()
    with closing(connect()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        previous = connection.execute("SELECT * FROM runs WHERE workflow=? AND digest=?", (workflow, digest)).fetchone()
        if previous:
            return {**public_run(previous), "replayed": True}
        try:
            result = parse_baseline(content) if workflow == "baseline" else parse_improved(content, get_mappings(connection))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        persist_records(connection, workflow, result)
        cursor = connection.execute("INSERT INTO runs(filename,workflow,digest,content,result) VALUES(?,?,?,?,?)",
                                    (file.filename or "upload.csv", workflow, digest, content, json.dumps(result)))
        return public_run(connection.execute("SELECT * FROM runs WHERE id=?", (cursor.lastrowid,)).fetchone())


class Approval(BaseModel):
    name: str = Field(min_length=1, max_length=60, pattern=r"^[A-Za-z][A-Za-z0-9 -]*$")
    fields: dict[str, str]
    ignored: list[str]
    date_format: Literal["%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y"]
    reviewer: str = Field(min_length=1, max_length=80)


@app.post("/api/runs/{run_id}/approve")
def approve(run_id: int, approval: Approval):
    with closing(connect()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Import run not found.")
        previous = json.loads(row["result"])
        if row["workflow"] != "improved" or previous["status"] != "awaiting_review":
            raise HTTPException(409, "Only a quarantined improved import can be approved; reload the run.")
        headers = previous["proposal"]["headers"]
        sources = list(approval.fields.values())
        if set(approval.fields) != set(FIELDS) or len(set(sources)) != 4 or any(source not in headers for source in sources):
            raise HTTPException(422, "Map all four canonical fields to distinct, existing source columns.")
        if len(set(approval.ignored)) != len(approval.ignored) or set(approval.ignored) != set(headers) - set(sources):
            raise HTTPException(422, "Explicitly acknowledge every unused source column in ignored.")
        if not approval.reviewer.strip():
            raise HTTPException(422, "Reviewer is required.")
        fingerprint = signature(headers)
        if connection.execute("SELECT 1 FROM mappings WHERE signature=?", (fingerprint,)).fetchone():
            raise HTTPException(409, "This schema was already approved on another run. Reprocess this run instead.")
        maximum = max((m["version"] for m in get_mappings(connection) if m["name"] == approval.name), default=0)
        config = {"name": approval.name, "version": maximum + 1, "headers": sorted(headers), "fields": approval.fields,
                  "ignored": approval.ignored, "date_format": approval.date_format, "source": "operator"}
        connection.execute("INSERT INTO mappings(name,version,signature,config,reviewer) VALUES(?,?,?,?,?)",
                           (config["name"], config["version"], fingerprint, json.dumps(config), approval.reviewer.strip()))
        result = parse_improved(row["content"], [config])
        result["approval"] = {"reviewer": approval.reviewer.strip(), "ignored": approval.ignored}
        persist_records(connection, "improved", result)
        save_result(connection, run_id, result)
        return public_run(connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone())


@app.post("/api/runs/{run_id}/reprocess")
def reprocess(run_id: int):
    with closing(connect()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Import run not found.")
        if row["workflow"] != "improved" or json.loads(row["result"])["status"] != "awaiting_review":
            raise HTTPException(409, "Only quarantined improved imports can be reprocessed.")
        result = parse_improved(row["content"], get_mappings(connection))
        persist_records(connection, "improved", result)
        save_result(connection, run_id, result)
        return public_run(connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone())
