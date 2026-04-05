from src.iso10110.ui.main import main


def test_streamlit_main_importable() -> None:
    assert callable(main)
