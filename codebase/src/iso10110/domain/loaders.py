from __future__ import annotations

from typing import Any

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
)
from .validation import SpecValidationException, validate_spec_v2


def _as_float(value: Any) -> float:
    return float(value)


def _load_surface(raw_surface: dict[str, Any]) -> Surface:
    raw_chamfer = raw_surface["chamfer"]
    return Surface(
        label=raw_surface["label"],
        radius=raw_surface["radius"],
        radius_display=raw_surface["radius_display"],
        r_kenn=raw_surface["r_kenn"],
        chamfer=Chamfer(
            width_mm=_as_float(raw_chamfer["width_mm"]),
            tolerance_mm=_as_float(raw_chamfer["tolerance_mm"]),
            angle_deg=_as_float(raw_chamfer["angle_deg"]),
            type=raw_chamfer["type"],
        ),
        figure_error=raw_surface["figure_error"],
        centering=raw_surface["centering"],
        surface_quality=raw_surface["surface_quality"],
        coating=raw_surface["coating"],
        coating_spec=raw_surface["coating_spec"],
    )


def load_spec_v2(raw: dict[str, Any]) -> SpecV2:
    errors = validate_spec_v2(raw)
    if errors:
        raise SpecValidationException(errors)

    title_block_raw = raw["title_block"]
    title_tolerances_raw = title_block_raw["tolerances"]
    title_block = TitleBlock(
        document_nr=title_block_raw["document_nr"],
        doc_type=title_block_raw["doc_type"],
        part_doc=title_block_raw["part_doc"],
        version=title_block_raw["version"],
        sheet=title_block_raw["sheet"],
        sheets_total=title_block_raw["sheets_total"],
        designation=title_block_raw["designation"],
        project_classification=title_block_raw["project_classification"],
        component_level=title_block_raw["component_level"],
        component_counter=title_block_raw["component_counter"],
        component_char=title_block_raw["component_char"],
        construction_group=title_block_raw["construction_group"],
        scale=title_block_raw["scale"],
        format=title_block_raw["format"],
        created_by=title_block_raw["created_by"],
        created_date=title_block_raw["created_date"],
        checked_by=title_block_raw["checked_by"],
        checked_date=title_block_raw["checked_date"],
        technical_by=title_block_raw["technical_by"],
        technical_date=title_block_raw["technical_date"],
        norm_by=title_block_raw["norm_by"],
        norm_date=title_block_raw["norm_date"],
        released_by=title_block_raw["released_by"],
        released_date=title_block_raw["released_date"],
        mass=title_block_raw["mass"],
        model_name=title_block_raw["model_name"],
        model_version=title_block_raw["model_version"],
        surface_treatment=title_block_raw["surface_treatment"],
        material_description=title_block_raw["material_description"],
        gs_required=title_block_raw["gs_required"],
        general_tolerance=title_block_raw["general_tolerance"],
        size_standard=title_block_raw["size_standard"],
        edge_standard=title_block_raw["edge_standard"],
        surface_standard=title_block_raw["surface_standard"],
        drawing_standard=title_block_raw["drawing_standard"],
        rohs_note=title_block_raw["rohs_note"],
        cz_position=title_block_raw["cz_position"],
        tolerances=Tolerances(
            plus_large=title_tolerances_raw["plus_large"],
            minus_large=title_tolerances_raw["minus_large"],
            plus_small=title_tolerances_raw["plus_small"],
            minus_small=title_tolerances_raw["minus_small"],
        ),
    )

    geometry_raw = raw["geometry"]
    geometry = Geometry(
        length_mm=_as_float(geometry_raw["length_mm"]),
        length_tol_plus=_as_float(geometry_raw["length_tol_plus"]),
        length_tol_minus=_as_float(geometry_raw["length_tol_minus"]),
        width_mm=_as_float(geometry_raw["width_mm"]),
        width_tol_plus=_as_float(geometry_raw["width_tol_plus"]),
        width_tol_minus=_as_float(geometry_raw["width_tol_minus"]),
        thickness_mm=_as_float(geometry_raw["thickness_mm"]),
        thickness_tol_plus=_as_float(geometry_raw["thickness_tol_plus"]),
        thickness_tol_minus=_as_float(geometry_raw["thickness_tol_minus"]),
        ca_x_mm=_as_float(geometry_raw["ca_x_mm"]),
        ca_y_mm=_as_float(geometry_raw["ca_y_mm"]),
    )

    parallelism_raw = raw["parallelism"]
    parallelism = Parallelism(
        value_mm=_as_float(parallelism_raw["value_mm"]),
        datum=parallelism_raw["datum"],
    )

    material_raw = raw["material"]
    material = Material(
        name=material_raw["name"],
        manufacturer=material_raw["manufacturer"],
        ne=_as_float(material_raw["ne"]),
        ve=_as_float(material_raw["ve"]),
        stress_birefringence=material_raw["stress_birefringence"],
        bubbles_inclusions=material_raw["bubbles_inclusions"],
        homogeneity_striae=material_raw["homogeneity_striae"],
    )

    surface_roughness_raw = raw["surface_roughness"]
    surface_roughness = SurfaceRoughness(
        rq_nm=_as_float(surface_roughness_raw["rq_nm"]),
        measurement_area=surface_roughness_raw["measurement_area"],
    )

    return SpecV2(
        spec_version=raw["spec_version"],
        substrate_type=raw["substrate_type"],
        title_block=title_block,
        geometry=geometry,
        parallelism=parallelism,
        material=material,
        left_surface=_load_surface(raw["left_surface"]),
        right_surface=_load_surface(raw["right_surface"]),
        surface_roughness=surface_roughness,
    )
