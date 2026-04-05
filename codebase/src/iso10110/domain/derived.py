from __future__ import annotations

from .model import SpecV2


GLASS_DENSITY_G_PER_CM3: dict[str, float] = {
    "N-BK7": 2.51,
    "N-BK10": 2.56,
    "N-K5": 2.59,
    "N-F2": 3.61,
    "N-SF11": 4.74,
    "N-SF6": 5.18,
    "N-BAK1": 3.19,
    "N-LAK22": 3.72,
    "N-LASF9": 4.44,
    "N-PK51": 3.68,
}


def compute_mass_g(spec: SpecV2) -> float:
    geometry = spec.geometry
    volume_cm3 = geometry.length_mm * geometry.width_mm * geometry.thickness_mm / 1000.0
    density = GLASS_DENSITY_G_PER_CM3.get(spec.material.name.strip(), 2.51)
    return round(volume_cm3 * density, 2)


def radius_display(radius: str) -> str:
    value = radius.strip()
    return f"R {value}" if value else ""


def apply_derived_fields(spec: SpecV2) -> None:
    spec.title_block.mass = f"{compute_mass_g(spec):.2f}"
    spec.left_surface.radius_display = radius_display(spec.left_surface.radius)
    spec.right_surface.radius_display = radius_display(spec.right_surface.radius)
