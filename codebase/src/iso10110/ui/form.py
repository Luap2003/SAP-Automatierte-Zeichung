from __future__ import annotations

from typing import Any

import streamlit as st

from ..config import load_default_spec_raw
from ..domain import apply_derived_fields, get_attr_path, set_attr_path, spec_to_pretty_json
from .state import (
    STATE_RAW_JSON_TEXT,
    get_spec,
    set_active_field_path,
    should_refresh_form,
)


FORM_CSS = """
<style>
[data-testid="stNumberInputStepDown"],
[data-testid="stNumberInputStepUp"] { display: none !important; }
</style>
"""


_DEFAULT_SPEC_RAW = load_default_spec_raw()


def _get_default_path(path: str) -> Any:
    obj: Any = _DEFAULT_SPEC_RAW
    for key in path.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def _sync_widget_value(widget_key: str, value: Any) -> None:
    if should_refresh_form() or widget_key not in st.session_state:
        st.session_state[widget_key] = value


def _commit_spec() -> None:
    spec = get_spec()
    apply_derived_fields(spec)
    st.session_state[STATE_RAW_JSON_TEXT] = spec_to_pretty_json(spec)


def _on_field_change(path: str, widget_key: str, as_number: bool = False) -> None:
    value = st.session_state[widget_key]
    set_attr_path(get_spec(), path, float(value) if as_number else value)
    if as_number:
        set_active_field_path(path)
    _commit_spec()


def _on_mirror_tol_change(plus_path: str, minus_path: str, widget_key: str) -> None:
    value = float(st.session_state[widget_key])
    set_attr_path(get_spec(), plus_path, value)
    set_attr_path(get_spec(), minus_path, value)
    set_active_field_path(plus_path)
    _commit_spec()


def _normalize_float(path: str) -> float:
    value = get_attr_path(get_spec(), path)
    try:
        return float(value)
    except (TypeError, ValueError):
        fallback = _get_default_path(path)
        try:
            normalized = float(fallback)
        except (TypeError, ValueError):
            normalized = 0.0
        set_attr_path(get_spec(), path, normalized)
        _commit_spec()
        return normalized


def _label(text: str) -> None:
    st.markdown(
        f"<p style='margin-top:10px;margin-bottom:0;font-size:14px'>{text}</p>",
        unsafe_allow_html=True,
    )


def _number(path: str, label: str = "", step: float = 0.1) -> None:
    widget_key = f"field__{path.replace('.', '__')}"
    _sync_widget_value(widget_key, _normalize_float(path))
    st.number_input(
        label or path,
        key=widget_key,
        step=step,
        label_visibility="visible" if label else "collapsed",
        on_change=_on_field_change,
        args=(path, widget_key, True),
    )


def _text(path: str) -> None:
    widget_key = f"field__{path.replace('.', '__')}"
    value = get_attr_path(get_spec(), path)
    _sync_widget_value(widget_key, "" if value is None else str(value))
    st.text_input(
        path,
        key=widget_key,
        label_visibility="collapsed",
        on_change=_on_field_change,
        args=(path, widget_key, False),
    )


def _number_mirror_tol(plus_path: str, minus_path: str, label: str = "", step: float = 0.01) -> None:
    widget_key = f"field__mirror_tol__{plus_path.replace('.', '__')}__{minus_path.replace('.', '__')}"
    _sync_widget_value(widget_key, _normalize_float(plus_path))
    st.number_input(
        label or plus_path,
        key=widget_key,
        step=step,
        label_visibility="visible" if label else "collapsed",
        on_change=_on_mirror_tol_change,
        args=(plus_path, minus_path, widget_key),
    )


def _row(label: str, path: str, field_type: str, step: float = 0.1) -> None:
    c_l, c_i = st.columns([1.8, 2.2])
    with c_l:
        _label(label)
    with c_i:
        if field_type == "number":
            _number(path, step=step)
        else:
            _text(path)


def _row_mirror_tol(label: str, val_path: str, plus_path: str, minus_path: str, val_step: float = 0.1, tol_step: float = 0.01) -> None:
    c_l, c_v, c_t = st.columns([1.8, 1.35, 1.15])
    with c_l:
        _label(label)
    with c_v:
        _number(val_path, step=val_step)
    with c_t:
        _number_mirror_tol(plus_path, minus_path, step=tol_step)


def _row_value_with_tol_slot(label: str, path: str, step: float = 0.1) -> None:
    c_l, c_v, c_t = st.columns([1.8, 1.35, 1.15])
    with c_l:
        _label(label)
    with c_v:
        _number(path, step=step)
    with c_t:
        st.markdown("&nbsp;", unsafe_allow_html=True)


def _row_chamfer(label: str, width_path: str, tol_path: str, angle_path: str, width_step: float = 0.1, tol_step: float = 0.05, angle_step: float = 1.0) -> None:
    c_l, c_w, c_t, c_a = st.columns([1.55, 1.0, 0.95, 0.85])
    with c_l:
        _label(label)
    with c_w:
        _number(width_path, label="Breite", step=width_step)
    with c_t:
        _number(tol_path, label="Tol", step=tol_step)
    with c_a:
        _number(angle_path, label="Winkel", step=angle_step)


def _row_dual_text(label: str, left_path: str, right_path: str, left_label: str = "links", right_label: str = "rechts") -> None:
    c_l, c_a, c_b = st.columns([1.55, 1.2, 1.2])
    with c_l:
        _label(label)
    with c_a:
        st.markdown(f"<p style='margin:0 0 6px 0;font-size:12px'>{left_label}</p>", unsafe_allow_html=True)
        _text(left_path)
    with c_b:
        st.markdown(f"<p style='margin:0 0 6px 0;font-size:12px'>{right_label}</p>", unsafe_allow_html=True)
        _text(right_path)


def _section(title: str) -> None:
    st.markdown(f"**{title}**")


def render_form_tab() -> None:
    spec = get_spec()
    st.caption("Formfelder aktualisieren die Zeichnung direkt. JSON-Tab bleibt synchron.")
    if st.button("Highlight zurücksetzen", width="stretch"):
        set_active_field_path(None)

    _section("Geometriedaten")
    h_label, h_value, h_tol = st.columns([1.8, 1.35, 1.15])
    with h_label:
        st.markdown("&nbsp;", unsafe_allow_html=True)
    with h_value:
        st.markdown("**Wert**")
    with h_tol:
        st.markdown("**Toleranz**")

    _row_mirror_tol("Länge / mm", "geometry.length_mm", "geometry.length_tol_plus", "geometry.length_tol_minus", val_step=0.1, tol_step=0.01)
    _row_mirror_tol("Breite / mm", "geometry.width_mm", "geometry.width_tol_plus", "geometry.width_tol_minus", val_step=0.1, tol_step=0.01)
    _row_mirror_tol("Substratdicke / mm", "geometry.thickness_mm", "geometry.thickness_tol_plus", "geometry.thickness_tol_minus", val_step=0.01, tol_step=0.001)
    _row_value_with_tol_slot("CA_x / mm", "geometry.ca_x_mm", step=0.1)
    _row_value_with_tol_slot("CA_y / mm", "geometry.ca_y_mm", step=0.1)
    _row_value_with_tol_slot("Parallelität", "parallelism.value_mm", step=0.001)

    st.divider()
    left_col, right_col = st.columns(2, gap="medium")
    with left_col:
        _section("Linke Fläche")
        _row("Radius", "left_surface.radius", "text")
        _row("R_Kenn", "left_surface.r_kenn", "text")
        _row_chamfer(
            "Schutzfase",
            "left_surface.chamfer.width_mm",
            "left_surface.chamfer.tolerance_mm",
            "left_surface.chamfer.angle_deg",
            width_step=0.1,
            tol_step=0.05,
            angle_step=1.0,
        )
        _row("Passe 3/", "left_surface.figure_error", "text")
        _row("Zentrierung 4/", "left_surface.centering", "text")
        _row("Sauberkeit 5/", "left_surface.surface_quality", "text")
        _row("Coating", "left_surface.coating", "text")

    with right_col:
        _section("Rechte Fläche")
        _row("Radius", "right_surface.radius", "text")
        _row("R_Kenn", "right_surface.r_kenn", "text")
        _row_chamfer(
            "Funktionsfase",
            "right_surface.chamfer.width_mm",
            "right_surface.chamfer.tolerance_mm",
            "right_surface.chamfer.angle_deg",
            width_step=0.1,
            tol_step=0.05,
            angle_step=1.0,
        )
        _row("Passe 3/", "right_surface.figure_error", "text")
        _row("Zentrierung 4/", "right_surface.centering", "text")
        _row("Sauberkeit 5/", "right_surface.surface_quality", "text")
        _row("Coating", "right_surface.coating", "text")

    st.divider()
    _section("Material")
    _row_dual_text("Name / Hersteller", "material.name", "material.manufacturer", left_label="Material", right_label="Hersteller")
    _row("0/", "material.stress_birefringence", "text")
    _row("1/", "material.bubbles_inclusions", "text")
    _row("2/", "material.homogeneity_striae", "text")
    st.caption(f"Masse (automatisch): {spec.title_block.mass} g")

    st.divider()
    _section("Grunddaten SAP")
    _row("Materialbezeichnung (DE + EN)", "title_block.material_description", "text")
