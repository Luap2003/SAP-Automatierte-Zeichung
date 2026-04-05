from __future__ import annotations

import json

import streamlit as st

from ..domain import SpecValidationException, apply_derived_fields, load_spec_v2, validate_spec_v2
from .state import STATE_RAW_JSON_TEXT, set_spec


def render_json_tab() -> None:
    st.caption("Roh-JSON bearbeiten und nur bei gültigem v2 JSON übernehmen.")
    st.text_area("JSON", key=STATE_RAW_JSON_TEXT, height=740)

    if st.button("JSON übernehmen", type="primary", width="stretch"):
        _apply_json_text(st.session_state[STATE_RAW_JSON_TEXT])


def _apply_json_text(raw_text: str) -> None:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        st.error(f"JSON Fehler: {exc}")
        return

    if not isinstance(parsed, dict):
        st.error("JSON muss ein Objekt auf oberster Ebene sein.")
        return

    errors = validate_spec_v2(parsed)
    if errors:
        st.error(f"Ungültige v2 Spezifikation ({len(errors)} Fehler):")
        for item in errors:
            st.markdown(f"- `{item.path}`: {item.message}")
        return

    try:
        spec = load_spec_v2(parsed)
    except SpecValidationException as exc:
        st.error("Spezifikation konnte nicht geladen werden.")
        for item in exc.errors:
            st.markdown(f"- `{item.path}`: {item.message}")
        return

    apply_derived_fields(spec)
    set_spec(spec, refresh_form=True)
    st.success("JSON erfolgreich übernommen.")
    st.rerun()
