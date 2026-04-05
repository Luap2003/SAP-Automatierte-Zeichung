from src.iso10110.cad import service as cad_service
from src.iso10110.config import load_default_spec


def test_cad_graceful_when_unavailable(monkeypatch) -> None:
    spec = load_default_spec()
    monkeypatch.setattr(cad_service, "cq", None)
    assert cad_service.has_cadquery() is False
    assert cad_service.build_cadquery_model(spec) is None


def test_cad_export_when_available() -> None:
    if not cad_service.has_cadquery():
        return

    spec = load_default_spec()
    model = cad_service.build_cadquery_model(spec)
    assert model is not None
    stl_bytes = cad_service.cadquery_model_to_bytes(model, "stl")
    assert len(stl_bytes) > 0
