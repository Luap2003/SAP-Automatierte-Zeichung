from __future__ import annotations

from typing import Iterable


FIELD_TAG_MAP: dict[str, list[str]] = {
    "geometry.length_mm": ["front.length_dim", "front.outer_horizontal"],
    "geometry.length_tol_plus": ["front.length_dim"],
    "geometry.length_tol_minus": ["front.length_dim"],
    "geometry.width_mm": ["front.width_dim", "front.outer_vertical"],
    "geometry.width_tol_plus": ["front.width_dim"],
    "geometry.width_tol_minus": ["front.width_dim"],
    "geometry.thickness_mm": ["side.thickness_dim", "side.thickness_edges"],
    "geometry.thickness_tol_plus": ["side.thickness_dim"],
    "geometry.thickness_tol_minus": ["side.thickness_dim"],
    "geometry.ca_x_mm": ["front.ca_rect", "front.ca_x_dim"],
    "geometry.ca_y_mm": ["front.ca_rect", "front.ca_y_dim"],
    "parallelism.value_mm": ["side.gt_frame"],
    "parallelism.datum": ["side.gt_frame"],
    "left_surface.chamfer.width_mm": ["front.left_chamfer_width"],
    "left_surface.chamfer.tolerance_mm": ["front.left_chamfer_width"],
    "left_surface.chamfer.angle_deg": ["front.left_chamfer_angle"],
    "right_surface.chamfer.width_mm": ["side.right_chamfer_width"],
    "right_surface.chamfer.tolerance_mm": ["side.right_chamfer_width"],
    "right_surface.chamfer.angle_deg": ["side.right_chamfer_angle"],
    "material.ne": ["info.material.ne"],
    "material.ve": ["info.material.ve"],
    "surface_roughness.rq_nm": ["info.surface_roughness.rq_nm"],
}


INFO_ROWS: list[tuple[str, str]] = [
    ("material.ne", "Brechzahl ne"),
    ("material.ve", "Abbe-Zahl ve"),
    ("surface_roughness.rq_nm", "Rauheit Rq [nm]"),
]


def active_tags_from_paths(active_paths: set[str]) -> set[str]:
    tags: set[str] = set()
    for path in active_paths:
        tags.update(FIELD_TAG_MAP.get(path, []))
    return tags


def tags_active(tags: Iterable[str], active_tags: set[str]) -> bool:
    return any(tag in active_tags for tag in tags)
