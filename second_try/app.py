import json
import math
import os
import tempfile
from copy import deepcopy
from io import BytesIO
from typing import Any, Dict, Iterable, Optional, Set, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle
import streamlit as st
import plotly.graph_objects as go

try:
    import cadquery as cq
except Exception:
    cq = None


DEFAULT_JSON = {
    "geometry": {
        "length_mm": 75,
        "length_tol_plus": 0.1,
        "length_tol_minus": 0.1,
        "width_mm": 65,
        "width_tol_plus": 0.1,
        "width_tol_minus": 0.1,
        "thickness_mm": 6,
        "thickness_tol_plus": 0.1,
        "thickness_tol_minus": 0.1,
        "ca_x_mm": 65,
        "ca_y_mm": 61,
    },
    "parallelism": {"value_mm": 0.05, "datum": "A"},
    "material": {
        "name": "N-BK7",
        "manufacturer": "Fa. Schott",
        "ne": 1.51872,
        "ve": 63.96,
        "stress_birefringence": "0/-",
        "bubbles_inclusions": "1/",
        "homogeneity_striae": "2/",
    },
    "left_surface": {
        "label": "linke Flaeche",
        "radius": "PL",
        "radius_display": "R PL",
        "r_kenn": "-",
        "chamfer": {"width_mm": 0.5, "tolerance_mm": 0.2, "angle_deg": 45, "type": "Schutzfase"},
        "figure_error": "3/-",
        "centering": "4/-",
        "surface_quality": "5/-",
        "coating": "-",
        "coating_spec": "",
    },
    "right_surface": {
        "label": "rechte Flaeche",
        "radius": "PL",
        "radius_display": "R PL",
        "r_kenn": "-",
        "chamfer": {"width_mm": 1.5, "tolerance_mm": 0.2, "angle_deg": 30, "type": "Funktionsfase"},
        "figure_error": "3/5 (2)",
        "centering": "4/-",
        "surface_quality": "5/ 10x0,063",
        "coating": "-",
        "coating_spec": "",
    },
    "surface_roughness": {"rq_nm": 1.2, "measurement_area": "P3"},
}


FIELD_TAG_MAP = {
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


FORM_FIELDS = [
    ("geometry.length_mm", "Länge [mm]", "number", 0.1),
    ("geometry.length_tol_plus", "Länge Toleranz + [mm]", "number", 0.01),
    ("geometry.length_tol_minus", "Länge Toleranz - [mm]", "number", 0.01),
    ("geometry.width_mm", "Breite [mm]", "number", 0.1),
    ("geometry.width_tol_plus", "Breite Toleranz + [mm]", "number", 0.01),
    ("geometry.width_tol_minus", "Breite Toleranz - [mm]", "number", 0.01),
    ("geometry.thickness_mm", "Dicke [mm]", "number", 0.1),
    ("geometry.thickness_tol_plus", "Dicke Toleranz + [mm]", "number", 0.01),
    ("geometry.thickness_tol_minus", "Dicke Toleranz - [mm]", "number", 0.01),
    ("geometry.ca_x_mm", "Prüfbereich X [mm]", "number", 0.1),
    ("geometry.ca_y_mm", "Prüfbereich Y [mm]", "number", 0.1),
    ("parallelism.value_mm", "Parallelität [mm]", "number", 0.01),
    ("parallelism.datum", "Parallelität Bezug", "text", None),
    ("material.name", "Material", "text", None),
    ("material.manufacturer", "Hersteller", "text", None),
    ("material.ne", "Brechzahl ne", "number", 0.00001),
    ("material.ve", "Abbe-Zahl ve", "number", 0.01),
    ("left_surface.chamfer.width_mm", "Linke Fase Breite [mm]", "number", 0.1),
    ("left_surface.chamfer.tolerance_mm", "Linke Fase Toleranz [mm]", "number", 0.01),
    ("left_surface.chamfer.angle_deg", "Linke Fase Winkel [°]", "number", 1.0),
    ("right_surface.chamfer.width_mm", "Rechte Fase Breite [mm]", "number", 0.1),
    ("right_surface.chamfer.tolerance_mm", "Rechte Fase Toleranz [mm]", "number", 0.01),
    ("right_surface.chamfer.angle_deg", "Rechte Fase Winkel [°]", "number", 1.0),
    ("surface_roughness.rq_nm", "Rauheit Rq [nm]", "number", 0.1),
]

INFO_ROWS = [
    ("material.ne", "Brechzahl ne"),
    ("material.ve", "Abbe-Zahl ve"),
    ("surface_roughness.rq_nm", "Rauheit Rq [nm]"),
]


def has_cadquery() -> bool:
    return cq is not None


def deep_copy_default() -> Dict[str, Any]:
    return deepcopy(DEFAULT_JSON)


def safe_get(spec: Dict[str, Any], path: str, default: float = 0.0) -> float:
    obj: Any = spec
    for key in path.split("."):
        obj = obj.get(key, None) if isinstance(obj, dict) else None
    try:
        return float(obj)
    except (TypeError, ValueError):
        return float(default)


def get_path(spec: Dict[str, Any], path: str) -> Any:
    obj: Any = spec
    for key in path.split("."):
        obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def get_default_path(path: str) -> Any:
    return get_path(DEFAULT_JSON, path)


def set_path(spec: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    obj = spec
    for key in parts[:-1]:
        if key not in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        obj = obj[key]
    obj[parts[-1]] = value


def active_tags_from_paths(active_paths: Set[str]) -> Set[str]:
    tags: Set[str] = set()
    for path in active_paths:
        tags.update(FIELD_TAG_MAP.get(path, []))
    return tags


def tags_active(tags: Iterable[str], active_tags: Set[str]) -> bool:
    return any(tag in active_tags for tag in tags)


def line_style(tags: Iterable[str], active_tags: Set[str], base_lw: float = 0.8) -> Dict[str, Any]:
    if tags_active(tags, active_tags):
        return {"color": "red", "linewidth": max(base_lw + 0.8, 1.2)}
    return {"color": "black", "linewidth": base_lw}


def text_style(tags: Iterable[str], active_tags: Set[str]) -> Dict[str, Any]:
    if tags_active(tags, active_tags):
        return {"color": "red", "fontweight": "bold"}
    return {"color": "black"}


def draw_dim_arrow(
    ax,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    text: str,
    tags: Iterable[str],
    active_tags: Set[str],
    text_offset=(0, 0),
    base_lw=1.0,
    text_rotation: Optional[float] = None,
):
    style = line_style(tags, active_tags, base_lw)
    tstyle = text_style(tags, active_tags)
    arrow = FancyArrowPatch(
        p1,
        p2,
        arrowstyle="<->",
        mutation_scale=10,
        linewidth=style["linewidth"],
        color=style["color"],
        shrinkA=0,
        shrinkB=0,
    )
    ax.add_patch(arrow)
    tx = (p1[0] + p2[0]) / 2 + text_offset[0]
    ty = (p1[1] + p2[1]) / 2 + text_offset[1]
    rotation = text_rotation
    if rotation is None:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        rotation = math.degrees(math.atan2(dy, dx))
    ax.text(
        tx,
        ty,
        text,
        fontsize=8,
        rotation=rotation,
        rotation_mode="anchor",
        ha="center",
        va="center",
        bbox=dict(facecolor="white", edgecolor="none", pad=0.5),
        **tstyle,
    )


def draw_line(ax, x1: float, y1: float, x2: float, y2: float, tags: Iterable[str], active_tags: Set[str], lw: float = 0.8):
    style = line_style(tags, active_tags, lw)
    ax.plot([x1, x2], [y1, y2], color=style["color"], linewidth=style["linewidth"])


def draw_text(ax, x: float, y: float, text: str, tags: Iterable[str], active_tags: Set[str], fontsize: float = 8, **kwargs):
    tstyle = text_style(tags, active_tags)
    ax.text(x, y, text, fontsize=fontsize, **tstyle, **kwargs)


def draw_front_view(ax_front, spec: Dict[str, Any], active_tags: Set[str], L: float, W: float, T: float, CAx: float, CAy: float):
    g = spec.get("geometry", {})
    left = spec.get("left_surface", {})

    left_ch = left.get("chamfer", {})
    ch = max(0.0, safe_get(spec, "left_surface.chamfer.width_mm", 0.5))
    ch = min(ch, L / 4, W / 4)

    def chamfered_rect_points(x0: float, y0: float, w: float, h: float, c: float):
        c_eff = min(max(0.0, c), w / 4, h / 4)
        return [
            (x0 + c_eff, y0 + h),
            (x0 + w - c_eff, y0 + h),
            (x0 + w, y0 + h - c_eff),
            (x0 + w, y0 + c_eff),
            (x0 + w - c_eff, y0),
            (x0 + c_eff, y0),
            (x0, y0 + c_eff),
            (x0, y0 + h - c_eff),
        ]

    contour_active = tags_active(["front.outer_horizontal", "front.outer_vertical"], active_tags)
    contour_color = "red" if contour_active else "black"
    contour_lw = 1.8 if contour_active else 1.0
    ax_front.add_patch(
        Polygon(chamfered_rect_points(0, 0, L, W, ch), closed=True, fill=False, linewidth=contour_lw, color=contour_color, zorder=3)
    )

    edge_inset = max(0.6, min(1.2, T * 0.15))
    ax_front.add_patch(
        Rectangle(
            (edge_inset, edge_inset),
            L - 2 * edge_inset,
            W - 2 * edge_inset,
            fill=False,
            linewidth=0.9,
            color="black",
            zorder=3,
        )
    )

    ca_x0 = (L - CAx) / 2
    ca_y0 = (W - CAy) / 2
    ca_rect_style = line_style(["front.ca_rect"], active_tags, 0.8)
    ax_front.add_patch(
        Rectangle(
            (ca_x0, ca_y0),
            CAx,
            CAy,
            fill=False,
            hatch="xx",
            linewidth=ca_rect_style["linewidth"],
            color=ca_rect_style["color"],
        )
    )

    draw_dim_arrow(ax_front, (ca_x0, -7), (ca_x0 + CAx, -7), f"{CAx:g}", ["front.ca_x_dim"], active_tags, text_offset=(0, -2), base_lw=0.8)
    draw_text(ax_front, (ca_x0 * 2 + CAx) / 2, -12.0, "Prüfbereich", ["front.ca_x_dim"], active_tags, fontsize=9, ha="center", va="center")
    draw_line(ax_front, ca_x0, 0, ca_x0, -9, ["front.ca_x_dim"], active_tags, 0.8)
    draw_line(ax_front, ca_x0 + CAx, 0, ca_x0 + CAx, -9, ["front.ca_x_dim"], active_tags, 0.8)
    draw_line(ax_front, L, 0, L, -9, ["front.ca_x_dim"], active_tags, 0.8)
    draw_dim_arrow(
        ax_front,
        (ca_x0 + CAx, -7),
        (L, -7),
        f"{(L - (ca_x0 + CAx)):g}",
        ["front.ca_x_dim"],
        active_tags,
        text_offset=(0, -2),
        base_lw=0.8,
    )

    draw_dim_arrow(
        ax_front,
        (0, -16),
        (L, -16),
        f"{L:g} +{g.get('length_tol_plus', 0):g} / -{g.get('length_tol_minus', 0):g}",
        ["front.length_dim"],
        active_tags,
        text_offset=(0, -2),
        base_lw=0.8,
    )
    draw_line(ax_front, 0, 0, 0, -16, ["front.length_dim"], active_tags, 0.8)
    draw_line(ax_front, L, 0, L, -16, ["front.length_dim"], active_tags, 0.8)

    draw_dim_arrow(ax_front, (L + 6, ca_y0), (L + 6, ca_y0 + CAy), f"{CAy:g}", ["front.ca_y_dim"], active_tags, text_offset=(2, 0), base_lw=0.8)
    draw_line(ax_front, L, ca_y0, L + 6, ca_y0, ["front.ca_y_dim"], active_tags, 0.8)
    draw_line(ax_front, L, ca_y0 + CAy, L + 6, ca_y0 + CAy, ["front.ca_y_dim"], active_tags, 0.8)
    draw_text(ax_front, L + 11.5, W / 2, "Prüfbereich", ["front.ca_y_dim"], active_tags, fontsize=9, rotation=90, va="center", ha="center")

    draw_dim_arrow(
        ax_front,
        (L + 13, 0),
        (L + 13, W),
        f"{W:g} +{g.get('width_tol_plus', 0):g} / -{g.get('width_tol_minus', 0):g}",
        ["front.width_dim"],
        active_tags,
        text_offset=(7, 0),
        base_lw=0.8,
    )
    draw_line(ax_front, L, 0, L + 13, 0, ["front.width_dim"], active_tags, 0.8)
    draw_line(ax_front, L, W, L + 13, W, ["front.width_dim"], active_tags, 0.8)

    p_a = (0.0, W - ch)
    p_b = (ch, W)
    d = (1.0 / (2**0.5), 1.0 / (2**0.5))
    n = (-1.0 / (2**0.5), 1.0 / (2**0.5))
    ext = 6.2
    a_ext = (p_a[0] + n[0] * ext, p_a[1] + n[1] * ext)
    b_ext = (p_b[0] + n[0] * ext, p_b[1] + n[1] * ext)
    draw_line(ax_front, p_a[0], p_a[1], a_ext[0], a_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    draw_line(ax_front, p_b[0], p_b[1], b_ext[0], b_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    draw_line(ax_front, a_ext[0], a_ext[1], b_ext[0], b_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    m = ((a_ext[0] + b_ext[0]) / 2, (a_ext[1] + b_ext[1]) / 2)
    draw_text(
        ax_front,
        m[0] + n[0] * 1,
        m[1] + n[1] * 1,
        f"{left_ch.get('width_mm', '-')} ±{left_ch.get('tolerance_mm', '-')}",
        ["front.left_chamfer_width"],
        active_tags,
        fontsize=8,
        rotation=55,
        ha="center",
        va="center",
    )
    draw_text(
        ax_front,
        m[0] + n[0] * 4.0,
        m[1] + n[1] * 4.0,
        "(4x)",
        ["front.left_chamfer_width"],
        active_tags,
        fontsize=8,
        rotation=55,
        ha="center",
        va="center",
    )

    left_angle = left_ch.get("angle_deg", 45)
    draw_line(ax_front, p_b[0], p_b[1], p_b[0] + d[0] * 7.2, p_b[1] + d[1] * 7.2, ["front.left_chamfer_angle"], active_tags, 0.8)
    draw_line(ax_front, p_b[0], p_b[1], p_b[0] + 10.2, p_b[1], ["front.left_chamfer_angle"], active_tags, 0.8)
    arc_style = line_style(["front.left_chamfer_angle"], active_tags, 0.8)
    ax_front.add_patch(Arc((p_b[0], p_b[1]), 9.4, 9.4, angle=0, theta1=0, theta2=45, linewidth=arc_style["linewidth"], color=arc_style["color"]))
    arrow_style = line_style(["front.left_chamfer_angle"], active_tags, 0.8)
    ax_front.add_patch(
        FancyArrowPatch((p_b[0] + 4.8, p_b[1] + 0.08), (p_b[0] + 4.25, p_b[1] + 0.08), arrowstyle="-|>", mutation_scale=8.2, linewidth=arrow_style["linewidth"], color=arrow_style["color"])
    )
    ax_front.add_patch(
        FancyArrowPatch((p_b[0] + 3.6, p_b[1] + 3.6), (p_b[0] + 3.2, p_b[1] + 3.2), arrowstyle="-|>", mutation_scale=8.2, linewidth=arrow_style["linewidth"], color=arrow_style["color"])
    )
    draw_text(ax_front, p_b[0] + 11.0, p_b[1] + 2.9, f"{left_angle}°", ["front.left_chamfer_angle"], active_tags, fontsize=8, rotation=-35, ha="left", va="center")

    ax_front.set_xlim(-22, L + 25)
    ax_front.set_ylim(-22, W + 18)
    ax_front.set_aspect("equal", adjustable="box")
    ax_front.axis("off")


def draw_side_view(ax_side, spec: Dict[str, Any], active_tags: Set[str], W: float, T: float):
    g = spec.get("geometry", {})
    right = spec.get("right_surface", {})
    rc = max(0.0, safe_get(spec, "right_surface.chamfer.width_mm", 0.0))
    rc_eff = min(rc, T / 2, W / 2)

    side_active = tags_active(["side.thickness_edges"], active_tags)
    side_color = "red" if side_active else "black"
    side_lw = 2.0 if side_active else 1.4
    side_poly = [(0, 0), (T, 0), (T, W - rc_eff), (T - rc_eff, W), (0, W)]
    ax_side.add_patch(Polygon(side_poly, closed=True, fill=False, hatch="//", linewidth=side_lw, color=side_color))
    draw_line(ax_side, T / 2, W * 0.25, T / 2, W * 0.78, ["side.thickness_edges"], active_tags, 0.8)

    ay = W * 0.58
    ax_side.add_patch(Rectangle((-10.5, ay - 3), 6.5, 6, fill=False, linewidth=0.8, color="black"))
    draw_text(ax_side, -7.25, ay, "A", [], active_tags, fontsize=9, ha="center", va="center")
    ax_side.add_patch(FancyArrowPatch((-4.0, ay), (0.0, ay), arrowstyle="-|>", mutation_scale=9, linewidth=0.8, color="black"))

    right_ch = right.get("chamfer", {})
    p1 = (T, W - rc_eff)
    p2 = (T - rc_eff, W)
    d_side = (1.0 / (2**0.5), -1.0 / (2**0.5))
    n_side = (1.0 / (2**0.5), 1.0 / (2**0.5))
    ext_side = 6.0
    p1_ext = (p1[0] + n_side[0] * ext_side, p1[1] + n_side[1] * ext_side)
    p2_ext = (p2[0] + n_side[0] * ext_side, p2[1] + n_side[1] * ext_side)
    draw_line(ax_side, p1[0], p1[1], p1_ext[0], p1_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    draw_line(ax_side, p2[0], p2[1], p2_ext[0], p2_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    draw_line(ax_side, p1_ext[0], p1_ext[1], p2_ext[0], p2_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    m_side = ((p1_ext[0] + p2_ext[0]) / 2, (p1_ext[1] + p2_ext[1]) / 2)
    draw_text(
        ax_side,
        m_side[0] + n_side[0] * 2.2,
        m_side[1] + n_side[1] * 2.2,
        f"{right_ch.get('width_mm', '-')} ±{right_ch.get('tolerance_mm', '-')}",
        ["side.right_chamfer_width"],
        active_tags,
        fontsize=8,
        rotation=-45,
        ha="left",
        va="center",
    )

    right_angle = right_ch.get("angle_deg", 30)
    corner = p2
    draw_line(ax_side, corner[0], corner[1], corner[0] + d_side[0] * 7.2, corner[1] + d_side[1] * 7.2, ["side.right_chamfer_angle"], active_tags, 0.8)
    draw_line(ax_side, corner[0], corner[1], corner[0] + 9.6, corner[1], ["side.right_chamfer_angle"], active_tags, 0.8)
    arc_style = line_style(["side.right_chamfer_angle"], active_tags, 0.8)
    ax_side.add_patch(Arc(corner, 9.0, 9.0, angle=0, theta1=315, theta2=360, linewidth=arc_style["linewidth"], color=arc_style["color"]))
    ax_side.add_patch(
        FancyArrowPatch((corner[0] + 4.6, corner[1] - 0.05), (corner[0] + 4.1, corner[1] - 0.05), arrowstyle="-|>", mutation_scale=8.5, linewidth=arc_style["linewidth"], color=arc_style["color"])
    )
    ax_side.add_patch(
        FancyArrowPatch((corner[0] + 3.25, corner[1] - 3.25), (corner[0] + 2.9, corner[1] - 2.9), arrowstyle="-|>", mutation_scale=8.5, linewidth=arc_style["linewidth"], color=arc_style["color"])
    )
    draw_text(ax_side, corner[0] + 10.1, corner[1] - 2.1, f"{right_angle}°", ["side.right_chamfer_angle"], active_tags, fontsize=11, rotation=35, ha="left", va="center")

    draw_dim_arrow(
        ax_side,
        (0, -8),
        (T, -8),
        f"{T:g} +{g.get('thickness_tol_plus', 0):g} / -{g.get('thickness_tol_minus', 0):g}",
        ["side.thickness_dim"],
        active_tags,
        text_offset=(0, -2),
    )
    draw_line(ax_side, 0, 0, 0, -8, ["side.thickness_dim"], active_tags, 0.8)
    draw_line(ax_side, T, 0, T, -8, ["side.thickness_dim"], active_tags, 0.8)

    gt_style = line_style(["side.gt_frame"], active_tags, 0.8)
    gt_text_style = text_style(["side.gt_frame"], active_tags)
    gt_x, gt_y = T + 7, -9
    ax_side.add_patch(Rectangle((gt_x, gt_y), 17, 5, fill=False, linewidth=gt_style["linewidth"], color=gt_style["color"]))
    ax_side.plot([gt_x + 4, gt_x + 4], [gt_y, gt_y + 5], color=gt_style["color"], linewidth=gt_style["linewidth"])
    ax_side.plot([gt_x + 11, gt_x + 11], [gt_y, gt_y + 5], color=gt_style["color"], linewidth=gt_style["linewidth"])
    ax_side.text(gt_x + 2, gt_y + 2.5, "//", fontsize=10, ha="center", va="center", **gt_text_style)
    ax_side.text(gt_x + 7.5, gt_y + 2.5, f"{spec.get('parallelism', {}).get('value_mm', 0.05):g}", fontsize=9, ha="center", va="center", **gt_text_style)
    ax_side.text(gt_x + 14, gt_y + 2.5, f"{spec.get('parallelism', {}).get('datum', 'A')}", fontsize=9, ha="center", va="center", **gt_text_style)

    ax_side.set_xlim(-13, T + 27)
    ax_side.set_ylim(-14, W + 14)
    ax_side.set_aspect("equal", adjustable="box")
    ax_side.axis("off")


def render(spec: Dict[str, Any], active_paths: Set[str]):
    L = safe_get(spec, "geometry.length_mm", 75)
    W = safe_get(spec, "geometry.width_mm", 65)
    T = safe_get(spec, "geometry.thickness_mm", 6)
    CAx = safe_get(spec, "geometry.ca_x_mm", L * 0.8)
    CAy = safe_get(spec, "geometry.ca_y_mm", W * 0.8)

    active_tags = active_tags_from_paths(active_paths)

    fig = plt.figure(figsize=(12, 6.8), dpi=120)
    gs = fig.add_gridspec(1, 2, width_ratios=[3.4, 1.9], wspace=0.28)
    ax_front = fig.add_subplot(gs[0, 0])
    ax_side = fig.add_subplot(gs[0, 1])

    draw_front_view(ax_front, spec, active_tags, L, W, T, CAx, CAy)
    draw_side_view(ax_side, spec, active_tags, W, T)

    return fig


def build_cadquery_model(spec: Dict[str, Any]):
    if not has_cadquery():
        return None

    L = max(0.1, safe_get(spec, "geometry.length_mm", 75))
    W = max(0.1, safe_get(spec, "geometry.width_mm", 65))
    T = max(0.1, safe_get(spec, "geometry.thickness_mm", 6))
    lc = max(0.0, safe_get(spec, "left_surface.chamfer.width_mm", 0.0))
    rc = max(0.0, safe_get(spec, "right_surface.chamfer.width_mm", 0.0))
    right_angle_deg = safe_get(spec, "right_surface.chamfer.angle_deg", 30.0)

    # Base optic body (centered at origin).
    wp = cq.Workplane("XY").box(L, W, T)

    # 4x corner chamfer around the plate contour.
    lc_eff = min(lc, L * 0.24, W * 0.24, T * 0.95)
    if lc_eff > 0:
        try:
            wp = wp.edges("|Z").chamfer(lc_eff)
        except Exception:
            pass

    # Single chamfer on one top side edge with configurable angle.
    # We model this via asymmetric chamfer distances on adjacent faces.
    rc_top = min(rc, L * 0.24, T * 0.95)
    rc_drop = rc_top * math.tan(math.radians(max(1.0, min(89.0, right_angle_deg))))
    rc_drop = max(0.05, min(rc_drop, W * 0.24, T * 0.95))
    if rc_top > 0:
        try:
            wp = wp.edges(">Y and >Z").chamfer(rc_top, rc_drop)
        except Exception:
            pass

    return wp


def cadquery_to_plotly_figure(model) -> go.Figure:
    shape = model.val()
    vertices, triangles = shape.tessellate(0.15, 0.2)
    x = [v.x for v in vertices]
    y = [v.y for v in vertices]
    z = [v.z for v in vertices]
    i = [tri[0] for tri in triangles]
    j = [tri[1] for tri in triangles]
    k = [tri[2] for tri in triangles]

    mesh = go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        color="#8fa6bf",
        opacity=1.0,
        flatshading=False,
        lighting=dict(ambient=0.5, diffuse=0.6, roughness=0.6, specular=0.2, fresnel=0.1),
        lightposition=dict(x=100, y=60, z=120),
    )

    fig = go.Figure(data=[mesh])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="data",
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.5, y=1.4, z=1.1)),
        ),
    )
    return fig


def cadquery_model_to_stl_bytes(model) -> bytes:
    shape = model.val()
    fd, path = tempfile.mkstemp(suffix=".stl")
    os.close(fd)
    try:
        shape.exportStl(path)
        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def sync_widget_value(widget_key: str, value: Any):
    if st.session_state.get("refresh_form", False) or widget_key not in st.session_state:
        st.session_state[widget_key] = value


def _serialize_spec(spec: Dict[str, Any]) -> str:
    return json.dumps(spec, indent=2, ensure_ascii=False)


def _on_number_change(path: str, widget_key: str):
    set_path(st.session_state["spec"], path, float(st.session_state[widget_key]))
    st.session_state["active_field_path"] = path
    st.session_state["raw_json_text"] = _serialize_spec(st.session_state["spec"])


def _on_text_change(path: str, widget_key: str):
    set_path(st.session_state["spec"], path, st.session_state[widget_key])
    st.session_state["raw_json_text"] = _serialize_spec(st.session_state["spec"])


def render_field(path: str, label: str, field_type: str, step: Optional[float]):
    value = get_path(st.session_state["spec"], path)
    widget_key = f"field__{path.replace('.', '__')}"
    mark_key = f"mark__{path.replace('.', '__')}"

    if field_type == "number":
        try:
            normalized_value = float(value)
        except (TypeError, ValueError):
            fallback = get_default_path(path)
            try:
                normalized_value = float(fallback)
            except (TypeError, ValueError):
                normalized_value = 0.0
            set_path(st.session_state["spec"], path, normalized_value)
            st.session_state["raw_json_text"] = _serialize_spec(st.session_state["spec"])

        sync_widget_value(widget_key, normalized_value)
        value_col, mark_col = st.columns([0.86, 0.14], gap="small")
        with value_col:
            st.number_input(
                label,
                key=widget_key,
                step=step if step is not None else 0.1,
                on_change=_on_number_change,
                args=(path, widget_key),
            )
        with mark_col:
            st.write("")
            st.write("")
            if st.button("Mark", key=mark_key, use_container_width=True):
                st.session_state["active_field_path"] = path
    else:
        normalized_value = "" if value is None else str(value)
        sync_widget_value(widget_key, normalized_value)
        st.text_input(
            label,
            key=widget_key,
            on_change=_on_text_change,
            args=(path, widget_key),
        )


def render_form_tab():
    st.caption("Formfelder aktualisieren die Zeichnung direkt. JSON-Tab bleibt synchron.")
    if st.button("Highlight zurücksetzen", use_container_width=True):
        st.session_state["active_field_path"] = None

    with st.expander("Geometrie", expanded=True):
        for path, label, field_type, step in FORM_FIELDS[:11]:
            render_field(path, label, field_type, step)

    with st.expander("Parallelität", expanded=True):
        for path, label, field_type, step in FORM_FIELDS[11:13]:
            render_field(path, label, field_type, step)

    with st.expander("Material", expanded=False):
        for path, label, field_type, step in FORM_FIELDS[13:17]:
            render_field(path, label, field_type, step)

    with st.expander("Linke Fläche / Fase", expanded=False):
        for path, label, field_type, step in FORM_FIELDS[17:20]:
            render_field(path, label, field_type, step)

    with st.expander("Rechte Fläche / Fase", expanded=False):
        for path, label, field_type, step in FORM_FIELDS[20:23]:
            render_field(path, label, field_type, step)

    with st.expander("Oberfläche", expanded=False):
        for path, label, field_type, step in FORM_FIELDS[23:]:
            render_field(path, label, field_type, step)


def render_json_tab():
    st.caption("Roh-JSON bearbeiten und nur bei gültigem JSON übernehmen.")
    st.text_area("JSON", key="raw_json_text", height=740)
    if st.button("JSON übernehmen", type="primary", use_container_width=True):
        try:
            parsed = json.loads(st.session_state["raw_json_text"])
            if not isinstance(parsed, dict):
                st.error("JSON muss ein Objekt auf oberster Ebene sein.")
                return
            st.session_state["spec"] = parsed
            st.session_state["active_field_path"] = None
            st.session_state["refresh_form"] = True
            st.session_state["raw_json_text"] = _serialize_spec(st.session_state["spec"])
            st.success("JSON erfolgreich übernommen.")
            st.rerun()
        except json.JSONDecodeError as exc:
            st.error(f"JSON Fehler: {exc}")


def init_state():
    if "spec" not in st.session_state:
        st.session_state["spec"] = deep_copy_default()
    if "active_field_path" not in st.session_state:
        st.session_state["active_field_path"] = None
    if "raw_json_text" not in st.session_state:
        st.session_state["raw_json_text"] = _serialize_spec(st.session_state["spec"])
    if "refresh_form" not in st.session_state:
        st.session_state["refresh_form"] = False


def render_info_block(spec: Dict[str, Any], active_tags: Set[str]):
    st.markdown("**Numerische Werte ohne direkte Geometrieabbildung**")
    rows = []
    for path, label in INFO_ROWS:
        value = get_path(spec, path)
        tags = FIELD_TAG_MAP.get(path, [])
        is_active = tags_active(tags, active_tags)
        color = "#d40000" if is_active else "#222"
        weight = "700" if is_active else "400"
        rows.append(
            f"<tr><td style='padding:4px 8px; color:{color}; font-weight:{weight}'>{label}</td>"
            f"<td style='padding:4px 8px; color:{color}; font-weight:{weight}; text-align:right'>{value}</td></tr>"
        )
    table = (
        "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
        "<thead><tr><th style='text-align:left; padding:4px 8px; border-bottom:1px solid #ddd'>Feld</th>"
        "<th style='text-align:right; padding:4px 8px; border-bottom:1px solid #ddd'>Wert</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    st.markdown(table, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Optik CAD Skizzen Generator", layout="wide")
    st.title("Optik CAD Skizzen Generator")
    st.caption("Links Formular/JSON bearbeiten, rechts wird die Zeichnung live erzeugt.")

    init_state()

    left_col, right_col = st.columns([1.2, 1.4])

    with left_col:
        st.subheader("Spezifikation")
        form_tab, json_tab = st.tabs(["Form", "JSON"])
        with form_tab:
            render_form_tab()
        with json_tab:
            render_json_tab()

    with right_col:
        st.subheader("Zeichnung")
        active_path = st.session_state.get("active_field_path")
        active_paths = {active_path} if active_path else set()
        active_tags = active_tags_from_paths(active_paths)

        try:
            fig = render(st.session_state["spec"], active_paths)
            st.pyplot(fig, clear_figure=True, use_container_width=True)

            svg_io = BytesIO()
            pdf_io = BytesIO()
            fig.savefig(svg_io, format="svg", bbox_inches="tight")
            fig.savefig(pdf_io, format="pdf", bbox_inches="tight")
            plt.close(fig)

            st.download_button(
                "Als SVG exportieren",
                data=svg_io.getvalue(),
                file_name="optik_skizze.svg",
                mime="image/svg+xml",
            )
            st.download_button(
                "Als PDF exportieren",
                data=pdf_io.getvalue(),
                file_name="optik_skizze.pdf",
                mime="application/pdf",
            )

            st.markdown("---")
            st.subheader("3D Modell (CadQuery)")
            if has_cadquery():
                model = build_cadquery_model(st.session_state["spec"])
                if model is not None:
                    model_fig = cadquery_to_plotly_figure(model)
                    st.plotly_chart(model_fig, use_container_width=True, config={"displaylogo": False})
                    st.download_button(
                        "Als STL exportieren",
                        data=cadquery_model_to_stl_bytes(model),
                        file_name="optik_koerper.stl",
                        mime="model/stl",
                    )
                else:
                    st.info("CadQuery-Modell konnte nicht erzeugt werden.")
            else:
                st.info("Für die 3D-Ansicht bitte `cadquery` installieren.")

            render_info_block(st.session_state["spec"], active_tags)

            if active_path:
                st.caption(f"Aktives Feld: `{active_path}`")
        except Exception as exc:
            st.error(f"Fehler beim Rendern: {exc}")
        finally:
            st.session_state["refresh_form"] = False


if __name__ == "__main__":
    main()
