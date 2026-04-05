import json
from typing import Any, Dict, Optional

import streamlit as st

from spec_utils import get_path, get_default_path, set_path


FORM_CSS = """
<style>
[data-testid="stNumberInputStepDown"],
[data-testid="stNumberInputStepUp"] { display: none !important; }
</style>
"""


def serialize_spec(spec: Dict[str, Any]) -> str:
    return json.dumps(spec, indent=2, ensure_ascii=False)


def sync_widget_value(widget_key: str, value: Any):
    if st.session_state.get("refresh_form", False) or widget_key not in st.session_state:
        st.session_state[widget_key] = value


def _on_field_change(path: str, widget_key: str, as_number: bool = False):
    val = st.session_state[widget_key]
    set_path(st.session_state["spec"], path, float(val) if as_number else val)
    if as_number:
        st.session_state["active_field_path"] = path
    st.session_state["raw_json_text"] = serialize_spec(st.session_state["spec"])


def _on_mirror_tol_change(plus_path: str, minus_path: str, widget_key: str):
    val = float(st.session_state[widget_key])
    set_path(st.session_state["spec"], plus_path, val)
    set_path(st.session_state["spec"], minus_path, val)
    st.session_state["active_field_path"] = plus_path
    st.session_state["raw_json_text"] = serialize_spec(st.session_state["spec"])


def _normalize_float(path: str) -> float:
    value = get_path(st.session_state["spec"], path)
    try:
        return float(value)
    except (TypeError, ValueError):
        fallback = get_default_path(path)
        try:
            nv = float(fallback)
        except (TypeError, ValueError):
            nv = 0.0
        set_path(st.session_state["spec"], path, nv)
        st.session_state["raw_json_text"] = serialize_spec(st.session_state["spec"])
        return nv


def _lbl(text: str) -> None:
    st.markdown(
        f"<p style='margin-top:10px;margin-bottom:0;font-size:14px'>{text}</p>",
        unsafe_allow_html=True,
    )


def _num(path: str, label: str = "", step: float = 0.1) -> None:
    widget_key = f"field__{path.replace('.', '__')}"
    sync_widget_value(widget_key, _normalize_float(path))
    st.number_input(
        label or path, key=widget_key, step=step,
        label_visibility="visible" if label else "collapsed",
        on_change=_on_field_change, args=(path, widget_key, True),
    )


def _txt(path: str) -> None:
    widget_key = f"field__{path.replace('.', '__')}"
    value = get_path(st.session_state["spec"], path)
    sync_widget_value(widget_key, "" if value is None else str(value))
    st.text_input(
        path, key=widget_key, label_visibility="collapsed",
        on_change=_on_field_change, args=(path, widget_key, False),
    )


def _num_mirror_tol(plus_path: str, minus_path: str, label: str = "", step: float = 0.01) -> None:
    widget_key = (
        f"field__mirror_tol__{plus_path.replace('.', '__')}__"
        f"{minus_path.replace('.', '__')}"
    )
    sync_widget_value(widget_key, _normalize_float(plus_path))
    st.number_input(
        label or plus_path, key=widget_key, step=step,
        label_visibility="visible" if label else "collapsed",
        on_change=_on_mirror_tol_change, args=(plus_path, minus_path, widget_key),
    )


def _row(label: str, path: str, field_type: str, step: Optional[float] = None) -> None:
    c_l, c_i = st.columns([1.8, 2.2])
    with c_l:
        _lbl(label)
    with c_i:
        if field_type == "number":
            _num(path, step=step or 0.1)
        else:
            _txt(path)


def _row_tol(label: str, val_path: str, plus_path: str, minus_path: str,
             val_step: float = 0.1, tol_step: float = 0.01) -> None:
    """Row: label | value | +tol | -tol"""
    c_l, c_v, c_p, c_m = st.columns([1.8, 1.5, 1.0, 1.0])
    with c_l:
        _lbl(label)
    with c_v:
        _num(val_path, step=val_step)
    with c_p:
        _num(plus_path, label="+", step=tol_step)
    with c_m:
        _num(minus_path, label="−", step=tol_step)


def _row_sym_tol(label: str, val_path: str, tol_path: str,
                 val_step: float = 0.1, tol_step: float = 0.1) -> None:
    """Row: label | value | ±tol"""
    c_l, c_v, c_t = st.columns([1.8, 1.5, 1.2])
    with c_l:
        _lbl(label)
    with c_v:
        _num(val_path, step=val_step)
    with c_t:
        _num(tol_path, label="±", step=tol_step)


def _row_mirror_tol(label: str, val_path: str, plus_path: str, minus_path: str,
                    val_step: float = 0.1, tol_step: float = 0.01) -> None:
    """Row: label | value | tol (writes to plus/minus)."""
    c_l, c_v, c_t = st.columns([1.8, 1.35, 1.15])
    with c_l:
        _lbl(label)
    with c_v:
        _num(val_path, step=val_step)
    with c_t:
        _num_mirror_tol(plus_path, minus_path, step=tol_step)


def _row_value_with_tol_slot(label: str, path: str, step: float = 0.1) -> None:
    """Row: label | value | (empty tolerance slot for table alignment)."""
    c_l, c_v, c_t = st.columns([1.8, 1.35, 1.15])
    with c_l:
        _lbl(label)
    with c_v:
        _num(path, step=step)
    with c_t:
        st.markdown("&nbsp;", unsafe_allow_html=True)


def _row_chamfer(label: str, width_path: str, tol_path: str, angle_path: str,
                 width_step: float = 0.1, tol_step: float = 0.05, angle_step: float = 1.0) -> None:
    """Row: label | width | tol | angle."""
    c_l, c_w, c_t, c_a = st.columns([1.55, 1.0, 0.95, 0.85])
    with c_l:
        _lbl(label)
    with c_w:
        _num(width_path, label="Breite", step=width_step)
    with c_t:
        _num(tol_path, label="Tol", step=tol_step)
    with c_a:
        _num(angle_path, label="Winkel", step=angle_step)


def _row_dual_text(label: str, left_path: str, right_path: str,
                   left_label: str = "links", right_label: str = "rechts") -> None:
    """Row: label | left text | right text."""
    c_l, c_a, c_b = st.columns([1.55, 1.2, 1.2])
    with c_l:
        _lbl(label)
    with c_a:
        st.markdown(f"<p style='margin:0 0 6px 0;font-size:12px'>{left_label}</p>", unsafe_allow_html=True)
        _txt(left_path)
    with c_b:
        st.markdown(f"<p style='margin:0 0 6px 0;font-size:12px'>{right_label}</p>", unsafe_allow_html=True)
        _txt(right_path)


def _sec(title: str) -> None:
    st.markdown(f"**{title}**")
