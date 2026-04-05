from __future__ import annotations

import math
from io import BytesIO
from typing import Iterable, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon, Rectangle
from matplotlib.figure import Figure

from ..drawing.scene import DrawingScene
from ..drawing.tags import tags_active


def _line_style(tags: Iterable[str], active_tags: set[str], base_lw: float = 0.9) -> dict[str, float | str]:
    if tags_active(tags, active_tags):
        return {"color": "#d62828", "linewidth": max(base_lw + 0.8, 1.2)}
    return {"color": "#111111", "linewidth": base_lw}


def _text_style(tags: Iterable[str], active_tags: set[str]) -> dict[str, str]:
    if tags_active(tags, active_tags):
        return {"color": "#d62828", "fontweight": "bold"}
    return {"color": "#111111"}


def _draw_dim_arrow(
    ax,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    text: str,
    tags: Iterable[str],
    active_tags: set[str],
    text_offset: tuple[float, float] = (0.0, 0.0),
    base_lw: float = 1.0,
    text_rotation: Optional[float] = None,
) -> None:
    style = _line_style(tags, active_tags, base_lw)
    tstyle = _text_style(tags, active_tags)
    ax.add_patch(
        FancyArrowPatch(
            p1,
            p2,
            arrowstyle="<->",
            mutation_scale=10,
            linewidth=style["linewidth"],
            color=style["color"],
            shrinkA=0,
            shrinkB=0,
        )
    )
    tx = (p1[0] + p2[0]) / 2 + text_offset[0]
    ty = (p1[1] + p2[1]) / 2 + text_offset[1]
    if text_rotation is None:
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        text_rotation = math.degrees(math.atan2(dy, dx))
    ax.text(
        tx,
        ty,
        text,
        fontsize=8,
        rotation=text_rotation,
        rotation_mode="anchor",
        ha="center",
        va="center",
        bbox=dict(facecolor="white", edgecolor="none", pad=0.5),
        **tstyle,
    )


def _draw_line(ax, x1: float, y1: float, x2: float, y2: float, tags: Iterable[str], active_tags: set[str], lw: float = 0.9) -> None:
    style = _line_style(tags, active_tags, lw)
    ax.plot([x1, x2], [y1, y2], color=style["color"], linewidth=style["linewidth"])


def _draw_text(
    ax,
    x: float,
    y: float,
    text: str,
    tags: Iterable[str],
    active_tags: set[str],
    fontsize: float = 8.0,
    **kwargs,
) -> None:
    ax.text(x, y, text, fontsize=fontsize, **_text_style(tags, active_tags), **kwargs)


def _draw_front_view(ax_front, scene: DrawingScene) -> None:
    spec = scene.spec
    active_tags = scene.active_tags
    g = spec.geometry
    L = scene.length_mm
    W = scene.width_mm
    T = scene.thickness_mm
    CAx = scene.ca_x_mm
    CAy = scene.ca_y_mm
    left_ch = spec.left_surface.chamfer
    ch = min(max(0.0, float(left_ch.width_mm)), L / 4, W / 4)

    def chamfered_rect_points(x0: float, y0: float, w: float, h: float, c: float) -> list[tuple[float, float]]:
        c = min(max(0.0, c), w / 4, h / 4)
        return [
            (x0 + c, y0 + h),
            (x0 + w - c, y0 + h),
            (x0 + w, y0 + h - c),
            (x0 + w, y0 + c),
            (x0 + w - c, y0),
            (x0 + c, y0),
            (x0, y0 + c),
            (x0, y0 + h - c),
        ]

    contour_active = tags_active(["front.outer_horizontal", "front.outer_vertical"], active_tags)
    ax_front.add_patch(
        Polygon(
            chamfered_rect_points(0, 0, L, W, ch),
            closed=True,
            fill=False,
            linewidth=1.8 if contour_active else 1.0,
            color="#d62828" if contour_active else "#111111",
            zorder=3,
        )
    )

    edge_inset = max(0.6, min(1.2, T * 0.15))
    ax_front.add_patch(Rectangle((edge_inset, edge_inset), L - 2 * edge_inset, W - 2 * edge_inset, fill=False, linewidth=0.9, color="#111111", zorder=3))

    ca_x0 = (L - CAx) / 2
    ca_y0 = (W - CAy) / 2
    ca_style = _line_style(["front.ca_rect"], active_tags, 0.8)
    ax_front.add_patch(
        Rectangle(
            (ca_x0, ca_y0),
            CAx,
            CAy,
            fill=False,
            hatch="xx",
            linewidth=ca_style["linewidth"],
            color=ca_style["color"],
        )
    )

    _draw_dim_arrow(ax_front, (ca_x0, -7), (ca_x0 + CAx, -7), f"{CAx:g}", ["front.ca_x_dim"], active_tags, text_offset=(0, -2), base_lw=0.8)
    _draw_text(ax_front, (ca_x0 * 2 + CAx) / 2, -12.0, "Prüfbereich", ["front.ca_x_dim"], active_tags, fontsize=9, ha="center", va="center")
    _draw_line(ax_front, ca_x0, 0, ca_x0, -9, ["front.ca_x_dim"], active_tags, 0.8)
    _draw_line(ax_front, ca_x0 + CAx, 0, ca_x0 + CAx, -9, ["front.ca_x_dim"], active_tags, 0.8)
    _draw_line(ax_front, L, 0, L, -9, ["front.ca_x_dim"], active_tags, 0.8)
    _draw_dim_arrow(
        ax_front,
        (ca_x0 + CAx, -7),
        (L, -7),
        f"{(L - (ca_x0 + CAx)):g}",
        ["front.ca_x_dim"],
        active_tags,
        text_offset=(0, -2),
        base_lw=0.8,
    )

    _draw_dim_arrow(
        ax_front,
        (0, -16),
        (L, -16),
        f"{L:g} +{g.length_tol_plus:g} / -{g.length_tol_minus:g}",
        ["front.length_dim"],
        active_tags,
        text_offset=(0, -2),
        base_lw=0.8,
    )
    _draw_line(ax_front, 0, 0, 0, -16, ["front.length_dim"], active_tags, 0.8)
    _draw_line(ax_front, L, 0, L, -16, ["front.length_dim"], active_tags, 0.8)

    _draw_dim_arrow(ax_front, (L + 6, ca_y0), (L + 6, ca_y0 + CAy), f"{CAy:g}", ["front.ca_y_dim"], active_tags, text_offset=(2, 0), base_lw=0.8)
    _draw_line(ax_front, L, ca_y0, L + 6, ca_y0, ["front.ca_y_dim"], active_tags, 0.8)
    _draw_line(ax_front, L, ca_y0 + CAy, L + 6, ca_y0 + CAy, ["front.ca_y_dim"], active_tags, 0.8)
    _draw_text(ax_front, L + 11.5, W / 2, "Prüfbereich", ["front.ca_y_dim"], active_tags, fontsize=9, rotation=90, va="center", ha="center")

    _draw_dim_arrow(
        ax_front,
        (L + 13, 0),
        (L + 13, W),
        f"{W:g} +{g.width_tol_plus:g} / -{g.width_tol_minus:g}",
        ["front.width_dim"],
        active_tags,
        text_offset=(7, 0),
        base_lw=0.8,
    )
    _draw_line(ax_front, L, 0, L + 13, 0, ["front.width_dim"], active_tags, 0.8)
    _draw_line(ax_front, L, W, L + 13, W, ["front.width_dim"], active_tags, 0.8)

    p_a = (0.0, W - ch)
    p_b = (ch, W)
    d = (1.0 / 2**0.5, 1.0 / 2**0.5)
    n = (-1.0 / 2**0.5, 1.0 / 2**0.5)
    ext = 6.2
    a_ext = (p_a[0] + n[0] * ext, p_a[1] + n[1] * ext)
    b_ext = (p_b[0] + n[0] * ext, p_b[1] + n[1] * ext)
    _draw_line(ax_front, p_a[0], p_a[1], a_ext[0], a_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    _draw_line(ax_front, p_b[0], p_b[1], b_ext[0], b_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    _draw_line(ax_front, a_ext[0], a_ext[1], b_ext[0], b_ext[1], ["front.left_chamfer_width"], active_tags, 0.8)
    m = ((a_ext[0] + b_ext[0]) / 2, (a_ext[1] + b_ext[1]) / 2)
    _draw_text(
        ax_front,
        m[0] + n[0] * 1,
        m[1] + n[1] * 1,
        f"{left_ch.width_mm:g} ±{left_ch.tolerance_mm:g}",
        ["front.left_chamfer_width"],
        active_tags,
        fontsize=8,
        rotation=55,
        ha="center",
        va="center",
    )
    _draw_text(ax_front, m[0] + n[0] * 4.0, m[1] + n[1] * 4.0, "(4x)", ["front.left_chamfer_width"], active_tags, fontsize=8, rotation=55, ha="center", va="center")

    left_angle = left_ch.angle_deg
    arc_style = _line_style(["front.left_chamfer_angle"], active_tags, 0.8)
    _draw_line(ax_front, p_b[0], p_b[1], p_b[0] + d[0] * 7.2, p_b[1] + d[1] * 7.2, ["front.left_chamfer_angle"], active_tags, 0.8)
    _draw_line(ax_front, p_b[0], p_b[1], p_b[0] + 10.2, p_b[1], ["front.left_chamfer_angle"], active_tags, 0.8)
    ax_front.add_patch(Arc((p_b[0], p_b[1]), 9.4, 9.4, angle=0, theta1=0, theta2=45, linewidth=arc_style["linewidth"], color=arc_style["color"]))
    ax_front.add_patch(
        FancyArrowPatch(
            (p_b[0] + 4.8, p_b[1] + 0.08),
            (p_b[0] + 4.25, p_b[1] + 0.08),
            arrowstyle="-|>",
            mutation_scale=8.2,
            linewidth=arc_style["linewidth"],
            color=arc_style["color"],
        )
    )
    ax_front.add_patch(
        FancyArrowPatch(
            (p_b[0] + 3.6, p_b[1] + 3.6),
            (p_b[0] + 3.2, p_b[1] + 3.2),
            arrowstyle="-|>",
            mutation_scale=8.2,
            linewidth=arc_style["linewidth"],
            color=arc_style["color"],
        )
    )
    _draw_text(ax_front, p_b[0] + 11.0, p_b[1] + 2.9, f"{left_angle:g}°", ["front.left_chamfer_angle"], active_tags, fontsize=8, rotation=-35, ha="left", va="center")

    ax_front.set_xlim(-22, L + 25)
    ax_front.set_ylim(-22, W + 18)
    ax_front.set_aspect("equal", adjustable="box")
    ax_front.axis("off")
    ax_front.set_title("Frontansicht", fontsize=10, loc="left")


def _draw_side_view(ax_side, scene: DrawingScene) -> None:
    spec = scene.spec
    active_tags = scene.active_tags
    g = spec.geometry
    W = scene.width_mm
    T = scene.thickness_mm
    right_ch = spec.right_surface.chamfer
    rc_eff = min(max(0.0, float(right_ch.width_mm)), T / 2, W / 2)

    side_active = tags_active(["side.thickness_edges"], active_tags)
    side_poly = [(0, 0), (T, 0), (T, W - rc_eff), (T - rc_eff, W), (0, W)]
    ax_side.add_patch(
        Polygon(
            side_poly,
            closed=True,
            fill=False,
            hatch="//",
            linewidth=2.0 if side_active else 1.4,
            color="#d62828" if side_active else "#111111",
        )
    )
    _draw_line(ax_side, T / 2, W * 0.25, T / 2, W * 0.78, ["side.thickness_edges"], active_tags, 0.8)

    ay = W * 0.58
    ax_side.add_patch(Rectangle((-10.5, ay - 3), 6.5, 6, fill=False, linewidth=0.8, color="#111111"))
    _draw_text(ax_side, -7.25, ay, "A", [], active_tags, fontsize=9, ha="center", va="center")
    ax_side.add_patch(FancyArrowPatch((-4.0, ay), (0.0, ay), arrowstyle="-|>", mutation_scale=9, linewidth=0.8, color="#111111"))

    p1 = (T, W - rc_eff)
    p2 = (T - rc_eff, W)
    d_side = (1.0 / 2**0.5, -1.0 / 2**0.5)
    n_side = (1.0 / 2**0.5, 1.0 / 2**0.5)
    ext_side = 6.0
    p1_ext = (p1[0] + n_side[0] * ext_side, p1[1] + n_side[1] * ext_side)
    p2_ext = (p2[0] + n_side[0] * ext_side, p2[1] + n_side[1] * ext_side)
    _draw_line(ax_side, p1[0], p1[1], p1_ext[0], p1_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    _draw_line(ax_side, p2[0], p2[1], p2_ext[0], p2_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    _draw_line(ax_side, p1_ext[0], p1_ext[1], p2_ext[0], p2_ext[1], ["side.right_chamfer_width"], active_tags, 0.8)
    m_side = ((p1_ext[0] + p2_ext[0]) / 2, (p1_ext[1] + p2_ext[1]) / 2)
    _draw_text(
        ax_side,
        m_side[0] + n_side[0] * 2.2,
        m_side[1] + n_side[1] * 2.2,
        f"{right_ch.width_mm:g} ±{right_ch.tolerance_mm:g}",
        ["side.right_chamfer_width"],
        active_tags,
        fontsize=8,
        rotation=-45,
        ha="left",
        va="center",
    )

    arc_style = _line_style(["side.right_chamfer_angle"], active_tags, 0.8)
    _draw_line(ax_side, p2[0], p2[1], p2[0] + d_side[0] * 7.2, p2[1] + d_side[1] * 7.2, ["side.right_chamfer_angle"], active_tags, 0.8)
    _draw_line(ax_side, p2[0], p2[1], p2[0] + 9.6, p2[1], ["side.right_chamfer_angle"], active_tags, 0.8)
    ax_side.add_patch(Arc(p2, 9.0, 9.0, angle=0, theta1=315, theta2=360, linewidth=arc_style["linewidth"], color=arc_style["color"]))
    ax_side.add_patch(
        FancyArrowPatch(
            (p2[0] + 4.6, p2[1] - 0.05),
            (p2[0] + 4.1, p2[1] - 0.05),
            arrowstyle="-|>",
            mutation_scale=8.5,
            linewidth=arc_style["linewidth"],
            color=arc_style["color"],
        )
    )
    ax_side.add_patch(
        FancyArrowPatch(
            (p2[0] + 3.25, p2[1] - 3.25),
            (p2[0] + 2.9, p2[1] - 2.9),
            arrowstyle="-|>",
            mutation_scale=8.5,
            linewidth=arc_style["linewidth"],
            color=arc_style["color"],
        )
    )
    _draw_text(ax_side, p2[0] + 10.1, p2[1] - 2.1, f"{right_ch.angle_deg:g}°", ["side.right_chamfer_angle"], active_tags, fontsize=11, rotation=35, ha="left", va="center")

    _draw_dim_arrow(
        ax_side,
        (0, -8),
        (T, -8),
        f"{T:g} +{g.thickness_tol_plus:g} / -{g.thickness_tol_minus:g}",
        ["side.thickness_dim"],
        active_tags,
        text_offset=(0, -2),
    )
    _draw_line(ax_side, 0, 0, 0, -8, ["side.thickness_dim"], active_tags, 0.8)
    _draw_line(ax_side, T, 0, T, -8, ["side.thickness_dim"], active_tags, 0.8)

    gt_style = _line_style(["side.gt_frame"], active_tags, 0.8)
    gt_text = _text_style(["side.gt_frame"], active_tags)
    gt_x, gt_y = T + 7, -9
    ax_side.add_patch(Rectangle((gt_x, gt_y), 17, 5, fill=False, linewidth=gt_style["linewidth"], color=gt_style["color"]))
    ax_side.plot([gt_x + 4, gt_x + 4], [gt_y, gt_y + 5], color=gt_style["color"], linewidth=gt_style["linewidth"])
    ax_side.plot([gt_x + 11, gt_x + 11], [gt_y, gt_y + 5], color=gt_style["color"], linewidth=gt_style["linewidth"])
    ax_side.text(gt_x + 2, gt_y + 2.5, "//", fontsize=10, ha="center", va="center", **gt_text)
    ax_side.text(gt_x + 7.5, gt_y + 2.5, f"{spec.parallelism.value_mm:g}", fontsize=9, ha="center", va="center", **gt_text)
    ax_side.text(gt_x + 14, gt_y + 2.5, spec.parallelism.datum, fontsize=9, ha="center", va="center", **gt_text)

    ax_side.set_xlim(-13, T + 27)
    ax_side.set_ylim(-14, W + 14)
    ax_side.set_aspect("equal", adjustable="box")
    ax_side.axis("off")
    ax_side.set_title("Seitenansicht", fontsize=10, loc="left")


def _draw_iso_table(ax, scene: DrawingScene) -> None:
    spec = scene.spec
    active_tags = scene.active_tags
    ax.axis("off")
    ax.set_title("ISO 10110 Werte", fontsize=10, loc="left")

    headers = [spec.left_surface.label, "Material", spec.right_surface.label]
    rows = [
        (spec.left_surface.radius_display, f"{spec.material.manufacturer} / {spec.material.name}", spec.right_surface.radius_display),
        (f"R_Kenn {spec.left_surface.r_kenn}", "", f"R_Kenn {spec.right_surface.r_kenn}"),
        (
            f"{spec.left_surface.chamfer.width_mm:g} ±{spec.left_surface.chamfer.tolerance_mm:g} x {spec.left_surface.chamfer.angle_deg:g}°",
            f"ne {spec.material.ne:g}",
            f"{spec.right_surface.chamfer.width_mm:g} ±{spec.right_surface.chamfer.tolerance_mm:g} x {spec.right_surface.chamfer.angle_deg:g}°",
        ),
        (spec.left_surface.figure_error, f"ve {spec.material.ve:g}", spec.right_surface.figure_error),
        (spec.left_surface.centering, spec.material.stress_birefringence, spec.right_surface.centering),
        (spec.left_surface.surface_quality, spec.material.bubbles_inclusions, spec.right_surface.surface_quality),
        ("l -", spec.material.homogeneity_striae, "l -"),
    ]

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="left",
        colLoc="center",
        loc="upper left",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#333333")
        if row == 0:
            cell.set_facecolor("#f2f2f2")
            cell.set_text_props(weight="bold")
            cell.set_linewidth(1.0)
        else:
            cell.set_linewidth(0.7)

    if tags_active(["info.material.ne"], active_tags):
        table[(3, 1)].get_text().set_color("#d62828")
        table[(3, 1)].get_text().set_weight("bold")
    if tags_active(["info.material.ve"], active_tags):
        table[(4, 1)].get_text().set_color("#d62828")
        table[(4, 1)].get_text().set_weight("bold")


def _draw_title_panel(ax, scene: DrawingScene) -> None:
    spec = scene.spec
    ax.axis("off")
    ax.set_title("Titelblock", fontsize=10, loc="left")

    lines = [
        f"Dokumenten-Nr.: {spec.title_block.document_nr}",
        f"Benennung: {spec.title_block.designation}",
        f"Version/Blatt: {spec.title_block.version} / {spec.title_block.sheet}",
        f"Maßstab/Format: {spec.title_block.scale} / {spec.title_block.format}",
        f"Werkstoff: {spec.title_block.material_description}",
        f"Masse [g]: {spec.title_block.mass}",
        f"Allg. Toleranz: {spec.title_block.general_tolerance}",
        f"Kantenstandard: {spec.title_block.edge_standard}",
        f"Oberflächenstandard: {spec.title_block.surface_standard}",
        f"Rauheit: Rq {spec.surface_roughness.rq_nm:g} ({spec.surface_roughness.measurement_area})",
    ]
    rohs_lines = spec.title_block.rohs_note.splitlines()

    y = 0.95
    for line in lines:
        ax.text(0.0, y, line, fontsize=8.3, ha="left", va="top", color="#111111")
        y -= 0.08

    y -= 0.04
    ax.text(0.0, y, "RoHS Hinweis:", fontsize=8.3, ha="left", va="top", weight="bold")
    y -= 0.07
    for line in rohs_lines:
        ax.text(0.0, y, line, fontsize=7.8, ha="left", va="top", color="#444444")
        y -= 0.06


def render_scene_to_figure(scene: DrawingScene) -> Figure:
    fig = plt.figure(figsize=(13.0, 8.4), dpi=120)
    outer = fig.add_gridspec(2, 1, height_ratios=[3.2, 2.0], hspace=0.24)
    top = outer[0].subgridspec(1, 2, width_ratios=[3.4, 1.9], wspace=0.28)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[2.2, 1.6], wspace=0.22)

    ax_front = fig.add_subplot(top[0, 0])
    ax_side = fig.add_subplot(top[0, 1])
    ax_table = fig.add_subplot(bottom[0, 0])
    ax_title = fig.add_subplot(bottom[0, 1])

    _draw_front_view(ax_front, scene)
    _draw_side_view(ax_side, scene)
    _draw_iso_table(ax_table, scene)
    _draw_title_panel(ax_title, scene)

    fig.suptitle("ISO 10110 - 2D Zeichnung", fontsize=13, y=0.99, fontweight="bold")
    return fig


def render_scene_to_svg(scene: DrawingScene) -> bytes:
    figure = render_scene_to_figure(scene)
    try:
        buffer = BytesIO()
        figure.savefig(buffer, format="svg", bbox_inches="tight")
        return buffer.getvalue()
    finally:
        plt.close(figure)


def render_scene_to_pdf(scene: DrawingScene) -> bytes:
    figure = render_scene_to_figure(scene)
    try:
        buffer = BytesIO()
        figure.savefig(buffer, format="pdf", bbox_inches="tight")
        return buffer.getvalue()
    finally:
        plt.close(figure)
