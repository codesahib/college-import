"""Strict original contract, kept executable for comparison."""
import csv
import io
from datetime import date

FIELDS = ("applicant_id", "year", "decision", "decision_date")
DECISIONS = {"admitted", "denied", "waitlisted"}


def read_csv(content: bytes):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Use UTF-8 encoded CSV.") from exc
    try:
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc
    if not rows or not rows[0]:
        raise ValueError("CSV needs a header row.")
    if len(rows) > 10001:
        raise ValueError("Maximum 10,000 data rows per import.")
    return rows[0], rows[1:]


def validate(values):
    errors = []
    applicant = values.get("applicant_id", "").strip()
    if not applicant or len(applicant) > 80:
        errors.append(("applicant_id", "Use a nonempty synthetic ID, at most 80 characters."))
    year = values.get("year", "").strip()
    # Bound conversion without changing the existing acceptance of leading zeroes.
    significant_year = year.lstrip("0")
    year_number = int(significant_year) if year.isascii() and year.isdigit() and len(significant_year) == 4 else None
    if year_number is None or not 2000 <= year_number <= 2100:
        errors.append(("year", "Expected a year from 2000 to 2100."))
    decision = values.get("decision", "").strip()
    if decision not in DECISIONS:
        errors.append(("decision", "Expected admitted, denied or waitlisted."))
    raw_date = values.get("decision_date", "").strip()
    try:
        parsed = date.fromisoformat(raw_date)
        if parsed.isoformat() != raw_date:
            raise ValueError()
    except ValueError:
        errors.append(("decision_date", "Expected a real date in YYYY-MM-DD format."))
    return {"applicant_id": applicant, "year": year_number if not any(e[0] == "year" for e in errors) else None,
            "decision": decision, "decision_date": raw_date}, errors


def parse_baseline(content: bytes):
    headers, rows = read_csv(content)
    if len(headers) != len(FIELDS) or set(headers) != set(FIELDS):
        return {"status": "schema_error", "accepted": [], "errors": [
            {"row": 1, "column": "header", "value": ",".join(headers),
             "message": "Expected headers: " + ", ".join(FIELDS)}],
            "total": len(rows), "rejected": len(rows), "mapping": "strict-v1", "drift": True}
    accepted, errors = [], []
    rejected = 0
    for number, cells in enumerate(rows, 2):
        if len(cells) != len(headers):
            rejected += 1
            errors.append({"row": number, "column": "row", "value": "", "message": "Column count differs from header."})
            continue
        values = dict(zip(headers, cells))
        record, issues = validate(values)
        if issues:
            rejected += 1
            errors.extend({"row": number, "column": field, "value": values.get(field, ""), "message": message}
                          for field, message in issues)
        else:
            accepted.append(record)
    return {"status": "completed", "accepted": accepted, "errors": errors, "total": len(rows),
            "rejected": rejected, "mapping": "strict-v1", "drift": False}
