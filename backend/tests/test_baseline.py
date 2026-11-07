from pathlib import Path
from backend.parser import parse_baseline

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_original_contract():
    result = parse_baseline((FIXTURES / "atlas_v1.csv").read_bytes())
    assert len(result["accepted"]) == 3
    assert result["rejected"] == 1
    assert result["errors"][0]["column"] == "year"


def test_changed_schema_is_known_shortcoming():
    result = parse_baseline((FIXTURES / "atlas_v2.csv").read_bytes())
    assert result["status"] == "schema_error"
    assert len(result["accepted"]) == 0
    assert result["rejected"] == 4
