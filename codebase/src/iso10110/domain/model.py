from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tolerances:
    plus_large: str
    minus_large: str
    plus_small: str
    minus_small: str


@dataclass
class TitleBlock:
    document_nr: str
    doc_type: str
    part_doc: str
    version: str
    sheet: str
    sheets_total: str
    designation: str
    project_classification: str
    component_level: str
    component_counter: str
    component_char: str
    construction_group: str
    scale: str
    format: str
    created_by: str
    created_date: str
    checked_by: str
    checked_date: str
    technical_by: str
    technical_date: str
    norm_by: str
    norm_date: str
    released_by: str
    released_date: str
    mass: str
    model_name: str
    model_version: str
    surface_treatment: str
    material_description: str
    gs_required: str
    general_tolerance: str
    size_standard: str
    edge_standard: str
    surface_standard: str
    drawing_standard: str
    rohs_note: str
    cz_position: str
    tolerances: Tolerances


@dataclass
class Geometry:
    length_mm: float
    length_tol_plus: float
    length_tol_minus: float
    width_mm: float
    width_tol_plus: float
    width_tol_minus: float
    thickness_mm: float
    thickness_tol_plus: float
    thickness_tol_minus: float
    ca_x_mm: float
    ca_y_mm: float


@dataclass
class Parallelism:
    value_mm: float
    datum: str


@dataclass
class Material:
    name: str
    manufacturer: str
    ne: float
    ve: float
    stress_birefringence: str
    bubbles_inclusions: str
    homogeneity_striae: str


@dataclass
class Chamfer:
    width_mm: float
    tolerance_mm: float
    angle_deg: float
    type: str


@dataclass
class Surface:
    label: str
    radius: str
    radius_display: str
    r_kenn: str
    chamfer: Chamfer
    figure_error: str
    centering: str
    surface_quality: str
    coating: str
    coating_spec: str


@dataclass
class SurfaceRoughness:
    rq_nm: float
    measurement_area: str


@dataclass
class SpecV2:
    spec_version: str
    substrate_type: str
    title_block: TitleBlock
    geometry: Geometry
    parallelism: Parallelism
    material: Material
    left_surface: Surface
    right_surface: Surface
    surface_roughness: SurfaceRoughness


@dataclass
class ValidationError:
    path: str
    message: str
