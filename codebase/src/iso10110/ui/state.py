from __future__ import annotations

import streamlit as st

from ..config import load_default_spec
from ..domain import SpecV2, apply_derived_fields, spec_to_pretty_json


STATE_SPEC = "spec"
STATE_ACTIVE_FIELD_PATH = "active_field_path"
STATE_RAW_JSON_TEXT = "raw_json_text"
STATE_REFRESH_FORM = "refresh_form"


def init_state() -> None:
    if STATE_SPEC not in st.session_state:
        spec = load_default_spec()
        apply_derived_fields(spec)
        st.session_state[STATE_SPEC] = spec
    if STATE_ACTIVE_FIELD_PATH not in st.session_state:
        st.session_state[STATE_ACTIVE_FIELD_PATH] = None
    if STATE_RAW_JSON_TEXT not in st.session_state:
        st.session_state[STATE_RAW_JSON_TEXT] = spec_to_pretty_json(st.session_state[STATE_SPEC])
    if STATE_REFRESH_FORM not in st.session_state:
        st.session_state[STATE_REFRESH_FORM] = False


def get_spec() -> SpecV2:
    return st.session_state[STATE_SPEC]


def set_spec(spec: SpecV2, refresh_form: bool = False) -> None:
    apply_derived_fields(spec)
    st.session_state[STATE_SPEC] = spec
    st.session_state[STATE_RAW_JSON_TEXT] = spec_to_pretty_json(spec)
    st.session_state[STATE_ACTIVE_FIELD_PATH] = None
    st.session_state[STATE_REFRESH_FORM] = refresh_form


def set_active_field_path(path: str | None) -> None:
    st.session_state[STATE_ACTIVE_FIELD_PATH] = path


def get_active_field_path() -> str | None:
    return st.session_state.get(STATE_ACTIVE_FIELD_PATH)


def set_refresh_form(value: bool) -> None:
    st.session_state[STATE_REFRESH_FORM] = value


def should_refresh_form() -> bool:
    return bool(st.session_state.get(STATE_REFRESH_FORM))
