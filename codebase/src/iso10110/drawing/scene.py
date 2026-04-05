from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.model import SpecV2


@dataclass
class DrawingScene:
    spec: SpecV2
    length_mm: float
    width_mm: float
    thickness_mm: float
    ca_x_mm: float
    ca_y_mm: float
    active_tags: set[str] = field(default_factory=set)
