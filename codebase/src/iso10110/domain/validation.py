from __future__ import annotations

from typing import Any, Mapping

from .model import ValidationError


Number = (int, float)


class SpecValidationException(ValueError):
    def __init__(self, errors: list[ValidationError]):
        self.errors = errors
        super().__init__("Spec v2 validation failed")


SPEC_TOP_LEVEL_KEYS = {
    "spec_version",
    "substrate_type",
    "title_block",
    "geometry",
    "parallelism",
    "material",
    "left_surface",
    "right_surface",
    "surface_roughness",
}


TITLE_BLOCK_FIELDS = {
    "document_nr": str,
    "doc_type": str,
    "part_doc": str,
    "version": str,
    "sheet": str,
    "sheets_total": str,
    "designation": str,
    "project_classification": str,
    "component_level": str,
    "component_counter": str,
    "component_char": str,
    "construction_group": str,
    "scale": str,
    "format": str,
    "created_by": str,
    "created_date": str,
    "checked_by": str,
    "checked_date": str,
    "technical_by": str,
    "technical_date": str,
    "norm_by": str,
    "norm_date": str,
    "released_by": str,
    "released_date": str,
    "mass": str,
    "model_name": str,
    "model_version": str,
    "surface_treatment": str,
    "material_description": str,
    "gs_required": str,
    "general_tolerance": str,
    "size_standard": str,
    "edge_standard": str,
    "surface_standard": str,
    "drawing_standard": str,
    "rohs_note": str,
    "cz_position": str,
    "tolerances": dict,
}


TITLE_TOLERANCE_FIELDS = {
    "plus_large": str,
    "minus_large": str,
    "plus_small": str,
    "minus_small": str,
}


GEOMETRY_FIELDS = {
    "length_mm": Number,
    "length_tol_plus": Number,
    "length_tol_minus": Number,
    "width_mm": Number,
    "width_tol_plus": Number,
    "width_tol_minus": Number,
    "thickness_mm": Number,
    "thickness_tol_plus": Number,
    "thickness_tol_minus": Number,
    "ca_x_mm": Number,
    "ca_y_mm": Number,
}


PARALLELISM_FIELDS = {
    "value_mm": Number,
    "datum": str,
}


MATERIAL_FIELDS = {
    "name": str,
    "manufacturer": str,
    "ne": Number,
    "ve": Number,
    "stress_birefringence": str,
    "bubbles_inclusions": str,
    "homogeneity_striae": str,
}


CHAMFER_FIELDS = {
    "width_mm": Number,
    "tolerance_mm": Number,
    "angle_deg": Number,
    "type": str,
}


SURFACE_FIELDS = {
    "label": str,
    "radius": str,
    "radius_display": str,
    "r_kenn": str,
    "chamfer": dict,
    "figure_error": str,
    "centering": str,
    "surface_quality": str,
    "coating": str,
    "coating_spec": str,
}


SURFACE_ROUGHNESS_FIELDS = {
    "rq_nm": Number,
    "measurement_area": str,
}


def _type_name(expected: type | tuple[type, ...]) -> str:
    if isinstance(expected, tuple):
        return " | ".join(sorted(tp.__name__ for tp in expected))
    return expected.__name__


def _is_number(value: Any) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def _validate_strict_object(
    obj: Any,
    path: str,
    field_types: Mapping[str, type | tuple[type, ...]],
    errors: list[ValidationError],
) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        errors.append(ValidationError(path, "expected object"))
        return None

    keys = set(obj.keys())
    missing = sorted(set(field_types.keys()) - keys)
    unknown = sorted(keys - set(field_types.keys()))

    for key in missing:
        errors.append(ValidationError(f"{path}.{key}", "missing required field"))
    for key in unknown:
        errors.append(ValidationError(f"{path}.{key}", "unknown field"))

    for key, expected in field_types.items():
        if key not in obj:
            continue
        value = obj[key]
        if expected == Number:
            if not _is_number(value):
                errors.append(ValidationError(f"{path}.{key}", "expected number"))
            continue

        if not isinstance(value, expected):
            errors.append(ValidationError(f"{path}.{key}", f"expected {_type_name(expected)}"))

    return obj


def validate_spec_v2(raw: dict[str, Any]) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if not isinstance(raw, dict):
        return [ValidationError("$", "expected object at top level")]

    keys = set(raw.keys())
    missing = sorted(SPEC_TOP_LEVEL_KEYS - keys)
    unknown = sorted(keys - SPEC_TOP_LEVEL_KEYS)

    for key in missing:
        errors.append(ValidationError(key, "missing required field"))
    for key in unknown:
        errors.append(ValidationError(key, "unknown field"))

    version = raw.get("spec_version")
    if version != "2.0":
        errors.append(ValidationError("spec_version", "must be exact string '2.0'"))

    if not isinstance(raw.get("substrate_type"), str):
        errors.append(ValidationError("substrate_type", "expected string"))

    title_block = _validate_strict_object(raw.get("title_block"), "title_block", TITLE_BLOCK_FIELDS, errors)
    if title_block is not None:
        _validate_strict_object(
            title_block.get("tolerances"),
            "title_block.tolerances",
            TITLE_TOLERANCE_FIELDS,
            errors,
        )

    _validate_strict_object(raw.get("geometry"), "geometry", GEOMETRY_FIELDS, errors)
    _validate_strict_object(raw.get("parallelism"), "parallelism", PARALLELISM_FIELDS, errors)
    _validate_strict_object(raw.get("material"), "material", MATERIAL_FIELDS, errors)

    left_surface = _validate_strict_object(raw.get("left_surface"), "left_surface", SURFACE_FIELDS, errors)
    if left_surface is not None:
        _validate_strict_object(left_surface.get("chamfer"), "left_surface.chamfer", CHAMFER_FIELDS, errors)

    right_surface = _validate_strict_object(raw.get("right_surface"), "right_surface", SURFACE_FIELDS, errors)
    if right_surface is not None:
        _validate_strict_object(right_surface.get("chamfer"), "right_surface.chamfer", CHAMFER_FIELDS, errors)

    _validate_strict_object(
        raw.get("surface_roughness"),
        "surface_roughness",
        SURFACE_ROUGHNESS_FIELDS,
        errors,
    )

    return errors
