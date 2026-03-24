#!/usr/bin/env python3
"""
ISO 10110 Optical Drawing → PDF Generator
==========================================
Renders a precise, ISO 10110-compliant technical drawing as a vector PDF
from JSON parameter input using reportlab.

Usage:
    python iso10110_generator.py input.json [output.pdf]

Layout (top to bottom):
    Upper half  — cross-section view with dimensions
    Middle band — ISO 10110 parameter table (linke Fläche | Material | rechte Fläche)
    Lower band  — standards box (left) + title block (right)
"""

import json
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from drawing_helpers import (
    F_LEFT, F_RIGHT, F_BOTTOM, F_TOP,
    C_BLACK, LW_MEDIUM, LW_THIN,
    draw_line,
)
from draw_border import draw_border
from draw_title_block import draw_title_block
from draw_cross_section import draw_cross_section, draw_dimensions
from draw_iso_table import draw_iso_table, draw_roughness_symbol, draw_standards_box


def load_data(json_path: str) -> dict:
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_pdf(json_path: str, output_path: str):
    data = load_data(json_path)

    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    c.setAuthor("ISO 10110 Generator")
    c.setTitle(f"ISO 10110 - {data['title_block']['designation']}")
    c.setSubject(data['title_block']['document_nr'])

    # 1. Border + zone markers
    draw_border(c)

    # ── Layout zones ──────────────────────────────────────────────
    # Frame: F_LEFT(20) → F_RIGHT(287), F_BOTTOM(10) → F_TOP(200)
    # Frame width = 267mm, height = 190mm
    #
    # Three horizontal bands:
    #   Lower  (10 → 68):  standards box (left) + title block (right)
    #   Middle (68 → 130): ISO 10110 parameter table
    #   Upper  (130→ 200): cross-section drawing
    frame_w = F_RIGHT - F_LEFT

    TB_H = 58.0
    lower_bottom = F_BOTTOM
    lower_top = lower_bottom + TB_H          # 68mm

    middle_bottom = lower_top
    # Table needs: 6mm header + 7*5.5mm rows = 44.5mm + padding
    middle_top = middle_bottom + 52.0         # 120mm

    upper_bottom = middle_top
    upper_top = F_TOP                         # 200mm

    # Separator lines between bands
    c.setStrokeColor(C_BLACK)
    draw_line(c, F_LEFT, lower_top, F_RIGHT, lower_top, lw=LW_MEDIUM)
    draw_line(c, F_LEFT, middle_top, F_RIGHT, middle_top, lw=LW_THIN)

    # ── 2. Lower band: title block (right) + standards box (left) ─
    tb_w = 180.0
    tb_x = F_RIGHT - tb_w
    draw_title_block(c, data, tb_x, lower_bottom, tb_w)

    stb_w = tb_x - F_LEFT
    draw_standards_box(c, data, F_LEFT, lower_bottom, stb_w, TB_H)

    # ── 3. Middle band: ISO parameter table ───────────────────────
    # y is the bottom of the header rect; header extends up by hdr_h (6mm)
    # Place header flush with top of middle band
    iso_header_bottom = middle_top - 6.0  # header top = middle_top
    draw_iso_table(c, data, F_LEFT, iso_header_bottom, frame_w)

    # ── 4. Upper band: cross-section drawing ──────────────────────
    # Available height = upper_top - upper_bottom (~80mm)
    # Need ~22mm above cross-section (chamfer labels, CA dim, tolerance frame)
    # Need ~14mm below cross-section (thickness dimension)
    upper_avail = upper_top - upper_bottom
    margin_above = 22.0
    margin_below = 14.0
    max_cs_h = upper_avail - margin_above - margin_below
    geo_h = data["geometry"]["width_mm"]
    scale = min(max_cs_h / geo_h, 1.2)

    cs_cx = F_LEFT + frame_w * 0.40
    cs_cy = upper_bottom + margin_below + (geo_h * scale) / 2.0

    coords = draw_cross_section(c, data, cs_cx, cs_cy, scale)
    draw_dimensions(c, data, coords)

    # ── 5. Roughness symbol (near cross-section) ─────────────────
    draw_roughness_symbol(c, data["surface_roughness"]["rq_nm"],
                          data["surface_roughness"]["measurement_area"],
                          coords["xr"] + 35, cs_cy + 12)

    c.save()
    print(f"PDF saved: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python iso10110_generator.py <input.json> [output.pdf]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else inp.replace(".json", "_drawing.pdf")
    generate_pdf(inp, out)
