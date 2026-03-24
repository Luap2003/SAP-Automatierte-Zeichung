"""Cross-section view and dimensioning for ISO 10110 drawings."""
import math
from drawing_helpers import *


def draw_cross_section(c, data: dict, cx: float, cy: float, scale: float):
    """
    Draw the substrate cross-section (rectangular for plane substrates).
    Returns coordinate dict for dimensioning.
    """
    geo = data["geometry"]
    ls  = data["left_surface"]
    rs  = data["right_surface"]

    w = geo["thickness_mm"] * scale
    h = geo["width_mm"] * scale

    xl = cx - w / 2
    xr = cx + w / 2
    yb = cy - h / 2
    yt = cy + h / 2

    # Chamfer geometry
    lc_w = ls["chamfer"]["width_mm"] * scale
    lc_a = ls["chamfer"]["angle_deg"]
    lc_h = lc_w * math.tan(math.radians(lc_a))
    rc_w = rs["chamfer"]["width_mm"] * scale
    rc_a = rs["chamfer"]["angle_deg"]
    rc_h = rc_w * math.tan(math.radians(rc_a))

    # Outline path with chamfers
    pts = [
        (xl + lc_w, yb),
        (xr - rc_w, yb),
        (xr, yb + rc_h),
        (xr, yt - rc_h),
        (xr - rc_w, yt),
        (xl + lc_w, yt),
        (xl, yt - lc_h),
        (xl, yb + lc_h),
    ]

    c.setStrokeColor(C_BLACK)
    c.setLineWidth(LW_THICK)
    path = c.beginPath()
    path.moveTo(pt(pts[0][0]), pt(pts[0][1]))
    for p in pts[1:]:
        path.lineTo(pt(p[0]), pt(p[1]))
    path.close()
    c.drawPath(path, stroke=1, fill=0)

    # Hatching
    c.setStrokeColor(C_GREY)
    c.setLineWidth(LW_HAIR)
    c.saveState()
    clip_path = c.beginPath()
    clip_path.moveTo(pt(pts[0][0]), pt(pts[0][1]))
    for p in pts[1:]:
        clip_path.lineTo(pt(p[0]), pt(p[1]))
    clip_path.close()
    c.clipPath(clip_path, stroke=0)

    spacing = HATCH_SPACING
    diag = math.sqrt(w**2 + h**2) * 1.5
    n_lines = int(diag / spacing) + 2
    angle_rad = math.radians(HATCH_ANGLE)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

    for i in range(-n_lines, n_lines):
        offset = i * spacing
        x1 = cx + offset * cos_a - diag * sin_a
        y1 = cy + offset * sin_a + diag * cos_a
        x2 = cx + offset * cos_a + diag * sin_a
        y2 = cy + offset * sin_a - diag * cos_a
        c.line(pt(x1), pt(y1), pt(x2), pt(y2))

    c.restoreState()
    c.setStrokeColor(C_BLACK)

    # Clear Aperture (dashed rectangle)
    ca_y = geo["ca_y_mm"] * scale
    ca_t = cy + ca_y / 2
    ca_b = cy - ca_y / 2
    c.setStrokeColor(C_GREEN)
    draw_dashed_line(c, xl, ca_t, xr, ca_t, lw=LW_THIN, dash=(3, 1.5))
    draw_dashed_line(c, xl, ca_b, xr, ca_b, lw=LW_THIN, dash=(3, 1.5))
    draw_dashed_line(c, xl - 0.3, ca_b, xl - 0.3, ca_t, lw=LW_HAIR, dash=(3, 1.5))
    draw_dashed_line(c, xr + 0.3, ca_b, xr + 0.3, ca_t, lw=LW_HAIR, dash=(3, 1.5))
    c.setStrokeColor(C_BLACK)

    draw_text(c, "Prüfbereich", xr + 3, ca_t - 1, size=1.8)
    draw_text(c, "Prüfbereich", xr + 3, ca_b - 1, size=1.8)
    for ay in [ca_t, ca_b]:
        draw_line(c, xr + 1, ay, xr + 2.5, ay, lw=LW_HAIR)

    # Datum A
    draw_datum_symbol(c, xl, cy, "A", side="left")

    return {
        "xl": xl, "xr": xr, "yb": yb, "yt": yt,
        "ca_t": ca_t, "ca_b": ca_b,
        "cx": cx, "cy": cy, "scale": scale,
        "w": w, "h": h,
    }


def draw_datum_symbol(c, x, y, label, side="left"):
    s = 2.5
    c.setStrokeColor(C_BLACK)
    c.setLineWidth(LW_THIN)

    if side == "left":
        path = c.beginPath()
        path.moveTo(pt(x), pt(y))
        path.lineTo(pt(x - s * 1.3), pt(y + s * 0.7))
        path.lineTo(pt(x - s * 1.3), pt(y - s * 0.7))
        path.close()
        c.drawPath(path, stroke=1, fill=0)
        bx = x - s * 1.3 - 7
        draw_line(c, x - s * 1.3, y, bx + 4, y, lw=LW_THIN)
    else:
        path = c.beginPath()
        path.moveTo(pt(x), pt(y))
        path.lineTo(pt(x + s * 1.3), pt(y + s * 0.7))
        path.lineTo(pt(x + s * 1.3), pt(y - s * 0.7))
        path.close()
        c.drawPath(path, stroke=1, fill=0)
        bx = x + s * 1.3 + 3
        draw_line(c, x + s * 1.3, y, bx, y, lw=LW_THIN)

    bs = 4
    bx_start = bx if side == "right" else x - s * 1.3 - bs - 3
    draw_rect(c, bx_start, y - bs / 2, bs, bs, lw=LW_THIN)
    draw_text(c, label, bx_start + bs / 2, y - 0.8, size=2.5, anchor="center")


def draw_dimensions(c, data: dict, coords: dict):
    """Add ISO-style dimensions to the cross-section."""
    geo = data["geometry"]
    xl, xr = coords["xl"], coords["xr"]
    yb, yt = coords["yb"], coords["yt"]
    cy = coords["cy"]
    sc = coords["scale"]
    ca_t, ca_b = coords["ca_t"], coords["ca_b"]

    c.setStrokeColor(C_RED)
    c.setFillColor(C_RED)

    # Thickness (horizontal, below)
    dim_y = yb - 10
    draw_dim_linear_h(c, xl, xr, dim_y, f"{geo['thickness_mm']}",
                      tol=f"±{geo['thickness_tol_plus']}")

    # Width (vertical, right side)
    dim_x1 = xr + 18
    draw_dim_linear_v(c, yb, yt, dim_x1,
                      f"{geo['width_mm']}",
                      tol=f"±{geo['width_tol_plus']}",
                      ext_from=xr)

    # Length (vertical, right side, second)
    dim_x2 = xr + 30
    draw_dim_linear_v(c, yb, yt, dim_x2,
                      f"{geo['length_mm']}",
                      tol=f"±{geo['length_tol_plus']}",
                      ext_from=xr)

    # Clear aperture y
    dim_x_ca = xr + 8
    draw_dim_linear_v(c, ca_b, ca_t, dim_x_ca,
                      f"{geo['ca_y_mm']}",
                      ext_from=xr)

    # Clear aperture x (horizontal, above)
    dim_y_ca = yt + 6
    ca_x_half = geo["ca_x_mm"] * sc / 2
    draw_dim_linear_h(c, coords["cx"] - ca_x_half, coords["cx"] + ca_x_half,
                      dim_y_ca, f"{geo['ca_x_mm']}")

    # Chamfer labels
    ls = data["left_surface"]["chamfer"]
    rs = data["right_surface"]["chamfer"]
    lc_text = f"{ls['width_mm']} ±{ls['tolerance_mm']} x {int(ls['angle_deg'])}°"
    draw_text(c, f"Schutzfasen {lc_text}", xl - 5, yt + 10, size=1.8, color=C_BLACK)
    lc_w_sc = ls["width_mm"] * sc
    draw_line(c, xl + lc_w_sc, yt, xl + 2, yt + 9, lw=LW_HAIR)
    c.setStrokeColor(C_RED)

    rc_text = f"{rs['width_mm']} ±{rs['tolerance_mm']} x {int(rs['angle_deg'])}°"
    draw_text(c, rc_text, xr + 3, yt + 10, size=1.8, color=C_BLACK)
    c.setStrokeColor(C_BLACK)
    draw_line(c, xr - rs["width_mm"] * sc, yt, xr - 1, yt + 9, lw=LW_HAIR)
    c.setStrokeColor(C_RED)

    # Parallelism tolerance frame
    par = data["parallelism"]
    draw_tolerance_frame(c, par["value_mm"], par["datum"], xr + 3, yt + 14)

    c.setStrokeColor(C_BLACK)
    c.setFillColor(C_BLACK)


def draw_dim_linear_h(c, x1, x2, y, value, tol="", ext_from_y=None):
    c.setStrokeColor(C_RED)
    c.setLineWidth(LW_THIN)
    if ext_from_y is not None:
        draw_line(c, x1, ext_from_y, x1, y - 1.5, lw=LW_HAIR)
        draw_line(c, x2, ext_from_y, x2, y - 1.5, lw=LW_HAIR)
    else:
        draw_line(c, x1, y + 3, x1, y - 1.5, lw=LW_HAIR)
        draw_line(c, x2, y + 3, x2, y - 1.5, lw=LW_HAIR)
    draw_line(c, x1, y, x2, y, lw=LW_THIN)
    a = 1.8
    aw = 0.5
    for ax, direction in [(x1, 1), (x2, -1)]:
        path = c.beginPath()
        path.moveTo(pt(ax), pt(y))
        path.lineTo(pt(ax + direction * a), pt(y + aw))
        path.lineTo(pt(ax + direction * a), pt(y - aw))
        path.close()
        c.setFillColor(C_RED)
        c.drawPath(path, stroke=0, fill=1)
    cx = (x1 + x2) / 2
    text = f"{value}"
    if tol:
        text += f" {tol}"
    draw_text(c, text, cx, y + 0.5, size=2.2, anchor="center", color=C_RED)


def draw_dim_linear_v(c, y1, y2, x, value, tol="", ext_from=None):
    c.setStrokeColor(C_RED)
    c.setLineWidth(LW_THIN)
    if ext_from is not None:
        draw_line(c, ext_from, y1, x + 1.5, y1, lw=LW_HAIR)
        draw_line(c, ext_from, y2, x + 1.5, y2, lw=LW_HAIR)
    draw_line(c, x, y1, x, y2, lw=LW_THIN)
    a = 1.8
    aw = 0.5
    for ay, direction in [(y1, 1), (y2, -1)]:
        path = c.beginPath()
        path.moveTo(pt(x), pt(ay))
        path.lineTo(pt(x + aw), pt(ay + direction * a))
        path.lineTo(pt(x - aw), pt(ay + direction * a))
        path.close()
        c.setFillColor(C_RED)
        c.drawPath(path, stroke=0, fill=1)
    cy = (y1 + y2) / 2
    text = f"{value}"
    if tol:
        text += f" {tol}"
    c.saveState()
    c.translate(pt(x - 1.5), pt(cy))
    c.rotate(90)
    font_size = 2.2 * mm * 0.85
    c.setFont("Helvetica", font_size)
    c.setFillColor(C_RED)
    tw = c.stringWidth(text, "Helvetica", font_size)
    c.drawString(-tw / 2, 0, text)
    c.restoreState()
    c.setFillColor(C_BLACK)


def draw_tolerance_frame(c, value, datum, x, y):
    c.setStrokeColor(C_BLACK)
    c.setLineWidth(LW_THIN)
    fh = 5
    cw = [7, 10, 5]
    cx = x
    for w in cw:
        draw_rect(c, cx, y, w, fh, lw=LW_THIN)
        cx += w
    sx = x + cw[0] / 2
    sy = y + fh / 2
    ll = 3
    gap = 1.0
    draw_line(c, sx - ll / 2, sy - gap / 2, sx + ll / 2, sy - gap / 2, lw=LW_THIN)
    draw_line(c, sx - ll / 2, sy + gap / 2, sx + ll / 2, sy + gap / 2, lw=LW_THIN)
    draw_text(c, str(value), x + cw[0] + cw[1] / 2, y + fh / 2 - 0.8,
              size=2.2, anchor="center")
    draw_text(c, datum, x + cw[0] + cw[1] + cw[2] / 2, y + fh / 2 - 0.8,
              size=2.2, anchor="center")
