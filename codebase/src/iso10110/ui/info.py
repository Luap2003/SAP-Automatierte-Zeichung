from __future__ import annotations

import streamlit as st

from ..domain import SpecV2, get_attr_path
from ..drawing import FIELD_TAG_MAP, INFO_ROWS, tags_active


def render_info_block(spec: SpecV2, active_tags: set[str]) -> None:
    st.markdown("**Numerische Werte ohne direkte Geometrieabbildung**")
    rows = []
    for path, label in INFO_ROWS:
        value = get_attr_path(spec, path)
        is_active = tags_active(FIELD_TAG_MAP.get(path, []), active_tags)
        color = "#d62828" if is_active else "#222"
        weight = "700" if is_active else "400"
        rows.append(
            f"<tr><td style='padding:4px 8px; color:{color}; font-weight:{weight}'>{label}</td>"
            f"<td style='padding:4px 8px; color:{color}; font-weight:{weight}; text-align:right'>{value}</td></tr>"
        )

    table = (
        "<table style='width:100%; border-collapse:collapse; border:1px solid #ddd;'>"
        "<thead><tr>"
        "<th style='text-align:left; padding:4px 8px; border-bottom:1px solid #ddd'>Feld</th>"
        "<th style='text-align:right; padding:4px 8px; border-bottom:1px solid #ddd'>Wert</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )
    st.markdown(table, unsafe_allow_html=True)
