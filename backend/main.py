import hashlib
import json
from contextlib import closing

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .db import connect, public_run, save_result
from .parser import parse_baseline

app = FastAPI(title="Admissions Import Maintenance Lab")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/runs")
def runs():
    with closing(connect()) as connection:
        return [public_run(row) for row in connection.execute("SELECT * FROM runs ORDER BY id DESC")]


@app.get("/api/records")
def records():
    with closing(connect()) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM records ORDER BY workflow, applicant_id, year")]


@app.post("/api/imports")
async def upload(file: UploadFile = File(...), workflow: str = "baseline"):
    if workflow != "baseline":
        raise HTTPException(400, "Unknown workflow.")
    content = await file.read(2_000_001)
    if len(content) > 2_000_000:
        raise HTTPException(413, "Maximum file size is 2 MB.")
    try:
        result = parse_baseline(content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    digest = hashlib.sha256(content).hexdigest()
    with closing(connect()) as connection, connection:
        previous = connection.execute("SELECT * FROM runs WHERE workflow=? AND digest=?", (workflow, digest)).fetchone()
        if previous:
            return {**public_run(previous), "replayed": True}
        inserted = 0
        for record in result["accepted"]:
            cursor = connection.execute("INSERT OR IGNORE INTO records VALUES (?,?,?,?,?)",
                                        (workflow, *record.values()))
            inserted += cursor.rowcount
        result.update(inserted=inserted, unchanged=len(result["accepted"]) - inserted)
        cursor = connection.execute("INSERT INTO runs(filename,workflow,digest,content,result) VALUES(?,?,?,?,?)",
                                    (file.filename or "upload.csv", workflow, digest, content, json.dumps(result)))
        save_result(connection, cursor.lastrowid, result)
        return public_run(connection.execute("SELECT * FROM runs WHERE id=?", (cursor.lastrowid,)).fetchone())
