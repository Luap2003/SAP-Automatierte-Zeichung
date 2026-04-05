from __future__ import annotations

import json
from importlib import resources
from typing import Any

from ..domain import apply_derived_fields, load_spec_v2
from ..domain.model import SpecV2


DEFAULTS_RESOURCE = "spec_defaults.v2.json"


def load_default_spec_raw() -> dict[str, Any]:
    with resources.files(__package__).joinpath(DEFAULTS_RESOURCE).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_default_spec() -> SpecV2:
    spec = load_spec_v2(load_default_spec_raw())
    apply_derived_fields(spec)
    return spec
