from __future__ import annotations

from ..domain.model import SpecV2

from .scene import DrawingScene


def build_scene(spec: SpecV2) -> DrawingScene:
    geometry = spec.geometry
    length_mm = max(0.1, float(geometry.length_mm))
    width_mm = max(0.1, float(geometry.width_mm))
    thickness_mm = max(0.1, float(geometry.thickness_mm))
    ca_x_mm = max(0.1, min(length_mm, float(geometry.ca_x_mm)))
    ca_y_mm = max(0.1, min(width_mm, float(geometry.ca_y_mm)))

    return DrawingScene(
        spec=spec,
        length_mm=length_mm,
        width_mm=width_mm,
        thickness_mm=thickness_mm,
        ca_x_mm=ca_x_mm,
        ca_y_mm=ca_y_mm,
    )
