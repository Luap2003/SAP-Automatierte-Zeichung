# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An ISO 10110 optical drawing PDF generator. Takes JSON input describing an optical component (glass substrate) and renders a standards-compliant technical drawing as a vector PDF using reportlab.

## Running

```bash
python3 iso10110_generator.py example_input.json [output.pdf]
```

If no output path is given, it defaults to `<input>_drawing.pdf`.

**Dependency:** `pip3 install reportlab` (the only external dependency).

## Architecture

All coordinates are in **millimeters**; `drawing_helpers.pt()` converts to reportlab points.

- **`iso10110_generator.py`** — Main entry point / layout orchestrator. Defines the three layout zones (upper: cross-section, middle: ISO table, lower: title block + standards box) and calls into the drawing modules.
- **`drawing_helpers.py`** — Shared constants (page margins, frame corners, line widths, colors) and primitive drawing functions (`draw_rect`, `draw_line`, `draw_text`, `draw_dashed_line`). Imported by all other modules.
- **`draw_border.py`** — Page border and ISO 5457 zone markers.
- **`draw_title_block.py`** — ISO 7200 title block. Accepts position (`tb_x`, `tb_y`) and width (`tb_w`) so the caller controls placement. Column widths scale proportionally to `tb_w`.
- **`draw_cross_section.py`** — Cross-section view (outline with chamfers, hatching, clear aperture), datum symbols, ISO 129 dimensioning (arrows, extension lines), and geometric tolerance frames. Returns a `coords` dict used by `draw_dimensions`.
- **`draw_iso_table.py`** — 3-column parameter table (linke Fläche | Material | rechte Fläche), surface roughness symbol (ISO 1302), and standards/tolerance reference box.

## Page Layout

A4 landscape (297×210mm). Drawing frame: left margin 20mm, others 10mm. The page is divided into three horizontal bands:

1. **Upper** — cross-section with red dimension annotations
2. **Middle** — ISO 10110 parameter table (header at top, rows grow downward)
3. **Lower** — standards box (left) + title block (right, 180mm wide, 58mm tall)

Layout zone positions are computed in `generate_pdf()` in `iso10110_generator.py`.

## JSON Input Structure

See `example_input.json` for the full schema. Top-level keys: `substrate_type`, `title_block`, `geometry`, `parallelism`, `material`, `left_surface`, `right_surface`, `surface_roughness`.

## Color Convention

- **Black** — borders, text, outlines
- **Red** — dimensions and tolerances
- **Grey** — labels and secondary text
- **Green** — clear aperture boundaries
