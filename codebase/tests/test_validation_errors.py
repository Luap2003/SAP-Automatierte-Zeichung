from copy import deepcopy

from src.iso10110.config import load_default_spec_raw
from src.iso10110.domain import validate_spec_v2


def test_validation_returns_structured_errors() -> None:
    raw = deepcopy(load_default_spec_raw())
    raw["spec_version"] = "1.0"
    raw["geometry"]["length_mm"] = "invalid"
    del raw["material"]["name"]

    errors = validate_spec_v2(raw)
    by_path = {item.path: item.message for item in errors}

    assert "spec_version" in by_path
    assert "geometry.length_mm" in by_path
    assert "material.name" in by_path
