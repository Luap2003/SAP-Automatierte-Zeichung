from .derived import apply_derived_fields, compute_mass_g
from .loaders import load_spec_v2
from .model import (
    Chamfer,
    Geometry,
    Material,
    Parallelism,
    SpecV2,
    Surface,
    SurfaceRoughness,
    TitleBlock,
    Tolerances,
    ValidationError,
)
from .serialization import dataclass_clone, get_attr_path, set_attr_path, spec_to_dict, spec_to_pretty_json
from .validation import SpecValidationException, validate_spec_v2

__all__ = [
    "Chamfer",
    "Geometry",
    "Material",
    "Parallelism",
    "SpecV2",
    "SpecValidationException",
    "Surface",
    "SurfaceRoughness",
    "TitleBlock",
    "Tolerances",
    "ValidationError",
    "apply_derived_fields",
    "compute_mass_g",
    "dataclass_clone",
    "get_attr_path",
    "load_spec_v2",
    "set_attr_path",
    "spec_to_dict",
    "spec_to_pretty_json",
    "validate_spec_v2",
]
