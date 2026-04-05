import matplotlib.pyplot as plt

from src.iso10110.config import load_default_spec
from src.iso10110.drawing import build_scene
from src.iso10110.rendering import render_scene_to_figure, render_scene_to_pdf, render_scene_to_svg


def test_scene_build_and_figure_render() -> None:
    spec = load_default_spec()
    scene = build_scene(spec)
    figure = render_scene_to_figure(scene)
    try:
        assert len(figure.axes) == 4
    finally:
        plt.close(figure)


def test_svg_and_pdf_exports_are_generated() -> None:
    scene = build_scene(load_default_spec())
    svg_bytes = render_scene_to_svg(scene)
    pdf_bytes = render_scene_to_pdf(scene)

    assert b"<svg" in svg_bytes[:400]
    assert pdf_bytes.startswith(b"%PDF")
