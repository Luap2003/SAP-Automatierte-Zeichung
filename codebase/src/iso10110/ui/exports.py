from __future__ import annotations

import base64
import json
from typing import Any

import streamlit as st

from ..domain import SpecV2, spec_to_dict
from ..drawing import DrawingScene
from ..rendering import render_scene_to_pdf, render_scene_to_svg


def render_2d_export_buttons(scene: DrawingScene) -> tuple[bytes, bytes]:
    svg_bytes = render_scene_to_svg(scene)
    st.download_button(
        "Als SVG exportieren",
        data=svg_bytes,
        file_name="optik_skizze.svg",
        mime="image/svg+xml",
    )

    pdf_bytes = render_scene_to_pdf(scene)
    st.download_button(
        "Als PDF exportieren",
        data=pdf_bytes,
        file_name="optik_zeichnung.pdf",
        mime="application/pdf",
    )
    return svg_bytes, pdf_bytes


def render_complete_export(spec: SpecV2, pdf_bytes: bytes, step_bytes: bytes | None) -> None:
    export_data: dict[str, Any] = {
        "user_id": 1,
        "spec": spec_to_dict(spec),
        "pdf": base64.b64encode(pdf_bytes).decode("ascii"),
    }
    if step_bytes is not None:
        export_data["step"] = base64.b64encode(step_bytes).decode("ascii")

    st.download_button(
        "Komplettexport (JSON)",
        data=json.dumps(export_data, indent=2, ensure_ascii=False),
        file_name="optik_export.json",
        mime="application/json",
    )
