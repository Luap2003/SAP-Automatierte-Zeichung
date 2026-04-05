from src.iso10110.config import load_default_spec, load_default_spec_raw
from src.iso10110.domain import validate_spec_v2


def test_defaults_file_is_valid_v2() -> None:
    raw = load_default_spec_raw()
    errors = validate_spec_v2(raw)
    assert errors == []


def test_defaults_can_be_loaded_to_dataclass() -> None:
    spec = load_default_spec()
    assert spec.spec_version == "2.0"
    assert spec.geometry.length_mm > 0
