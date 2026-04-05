from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from ..cad import build_cadquery_model, cadquery_model_to_bytes, cadquery_to_plotly_figure, has_cadquery
from ..drawing import active_tags_from_paths, build_scene
from ..rendering import render_scene_to_figure
from .exports import render_2d_export_buttons, render_complete_export
from .form import FORM_CSS, render_form_tab
from .info import render_info_block
from .json_editor import render_json_tab
from .state import (
    get_active_field_path,
    get_spec,
    init_state,
    set_refresh_form,
)


def main() -> None:
    st.set_page_config(page_title="Optik CAD Skizzen Generator", layout="wide")
    st.title("Optik CAD Skizzen Generator")
    st.markdown(FORM_CSS, unsafe_allow_html=True)
    st.caption("Links Formular/JSON bearbeiten, rechts wird die Zeichnung live erzeugt.")

    init_state()

    left_col, right_col = st.columns([1.2, 1.4])

    with left_col:
        st.subheader("Spezifikation")
        form_tab, json_tab = st.tabs(["Form", "JSON"])
        with form_tab:
            render_form_tab()
        with json_tab:
            render_json_tab()

    with right_col:
        st.subheader("Zeichnung")
        active_path = get_active_field_path()
        active_paths = {active_path} if active_path else set()
        active_tags = active_tags_from_paths(active_paths)

        try:
            spec = get_spec()
            scene = build_scene(spec)
            scene.active_tags = active_tags

            figure = render_scene_to_figure(scene)
            st.pyplot(figure, clear_figure=True, use_container_width=True)
            plt.close(figure)

            _, pdf_bytes = render_2d_export_buttons(scene)

            st.markdown("---")
            st.subheader("3D Modell (CadQuery)")
            step_bytes = None
            if has_cadquery():
                model = build_cadquery_model(spec)
                if model is not None:
                    st.plotly_chart(cadquery_to_plotly_figure(model), use_container_width=True, config={"displaylogo": False})
                    step_bytes = cadquery_model_to_bytes(model, "step")
                    st.download_button(
                        "Als STL exportieren",
                        data=cadquery_model_to_bytes(model, "stl"),
                        file_name="optik_koerper.stl",
                        mime="model/stl",
                    )
                else:
                    st.info("CadQuery-Modell konnte nicht erzeugt werden.")
            else:
                st.info("Für die 3D-Ansicht bitte `cadquery` installieren.")

            st.markdown("---")
            render_complete_export(spec, pdf_bytes, step_bytes)
            render_info_block(spec, active_tags)

            if active_path:
                st.caption(f"Aktives Feld: `{active_path}`")
        except Exception as exc:
            st.error(f"Fehler beim Rendern: {exc}")
        finally:
            set_refresh_form(False)


if __name__ == "__main__":
    main()
