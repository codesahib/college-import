"""Declarative schema detection; no fuzzy matching or executable mappings."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .parser import FIELDS, read_csv, validate

CONFIG = json.loads(Path(__file__).with_name("mappings.json").read_text())
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y")


def header_key(value):
    return "_".join(value.strip().lower().split())


def signature(headers):
    return hashlib.sha256(json.dumps(sorted(headers)).encode()).hexdigest()


def initial_mappings():
    return [{**mapping, "headers": sorted(mapping["fields"].values()), "ignored": [], "source": "configured"}
            for mapping in CONFIG["mappings"]]


def parse_improved(content, mappings):
    original, rows = read_csv(content)
    headers = [header_key(h) for h in original]
    result = {"accepted": [], "accepted_rows": [], "errors": [], "total": len(rows),
              "rejected": 0, "held": 0, "drift": set(headers) != set(FIELDS), "mapping": None}
    if any(not h for h in headers) or len(set(headers)) != len(headers):
        result.update(status="schema_error", rejected=len(rows), drift=True)
        result["errors"] = [{"row": 1, "column": "header", "value": ",".join(original),
                             "message": "Headers must be nonempty and unique after case/space normalization."}]
        return result
    found = next((m for m in mappings if sorted(m["headers"]) == sorted(headers)), None)
    if found is None:
        candidates = {field: [h for h in headers if h in aliases + CONFIG["review_only_aliases"].get(field, [])]
                      for field, aliases in CONFIG["header_aliases"].items()}
        proposed = {field: options[0] if len(options) == 1 else "" for field, options in candidates.items()}
        used = set(proposed.values()) - {""}
        issues = []
        for field, options in candidates.items():
            if len(options) != 1:
                issues.append({"row": 1, "column": field, "value": ", ".join(options),
                               "message": "Multiple plausible columns; choose explicitly." if options else "No recognized header; select a source column."})
        review_only = [field for field, source in proposed.items() if source in CONFIG["review_only_aliases"].get(field, [])]
        for field in review_only:
            issues.append({"row": 1, "column": field, "value": proposed[field], "message": "This column has a different business meaning; explicit operator review required."})
        if len(used) != len(FIELDS) or used != set(headers) or review_only:
            if set(headers) - used:
                issues.append({"row": 1, "column": "header", "value": ", ".join(h for h in headers if h not in used),
                               "message": "Review unused columns. Approval explicitly records ignored columns."})
            result.update(status="awaiting_review", held=len(rows), errors=issues, drift=True,
                          proposal={"headers": headers, "fields": proposed, "candidates": candidates,
                                    "date_format": "%Y-%m-%d", "sample": [dict(zip(headers, row)) for row in rows[:3]]})
            return result
        # Only unique, complete aliases with an ISO date contract are automatic.
        found = {"name": "Aliases", "version": CONFIG["version"], "fields": proposed, "headers": sorted(headers),
                 "ignored": [], "date_format": "%Y-%m-%d", "source": "aliases"}
    result.update(status="completed", mapping=f'{found["name"]}@{found["version"]}', mapping_config=found)
    for number, cells in enumerate(rows, 2):
        if len(cells) != len(headers):
            result["rejected"] += 1
            result["errors"].append({"row": number, "column": "row", "value": str(len(cells)),
                                     "message": f"Expected {len(headers)} columns, received {len(cells)}."})
            continue
        raw = dict(zip(headers, cells))
        values = {field: raw[source].strip() for field, source in found["fields"].items()}
        values["decision"] = CONFIG["decision_aliases"].get(values["decision"].casefold(), values["decision"])
        source_date = values["decision_date"]
        date_error = False
        try:
            parsed = datetime.strptime(source_date, found["date_format"])
            if parsed.strftime(found["date_format"]) != source_date:
                raise ValueError()
            values["decision_date"] = parsed.date().isoformat()
        except ValueError:
            date_error = True
            values["decision_date"] = ""
        record, issues = validate(values)
        if issues:
            result["rejected"] += 1
            for field, message in issues:
                source = found["fields"][field]
                if field == "decision_date" and date_error:
                    message = f'Expected a real date matching {found["date_format"]}; confirm the vendor contract.'
                result["errors"].append({"row": number, "column": source, "field": field, "value": raw[source], "message": message})
        else:
            result["accepted"].append(record)
            result["accepted_rows"].append(number)
    return result
