"""Run from the repository root: python scripts/diagnose.py."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.parser import parse_baseline

expected = json.loads((ROOT / "fixtures/expected.json").read_text())
report = []
for name, truth in expected.items():
    result = parse_baseline((ROOT / "fixtures" / name).read_bytes())
    report.append({"file": name, "valid_rows": truth["valid"], "invalid_rows": truth["invalid"],
                   "accepted": len(result["accepted"]), "rejected": result["rejected"],
                   "status": result["status"], "errors": result["errors"]})
destination = ROOT / "evidence/baseline-diagnosis.json"
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
