"""Test dymny aplikacji na plikach do pokazu; wymaga modeli z Release models-v1 w models/."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import model_store

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"
DEMO = sorted((ROOT / "app" / "demo").glob("*.csv"))


def models_available() -> bool:
    try:
        metadata = model_store.load_metadata()
    except FileNotFoundError:
        return False
    return all((model_store.MODELS_DIR / e["file"]).exists() for e in metadata["pipelines"])


pytestmark = pytest.mark.skipif(not models_available(),
                                reason="brak plików .joblib z Release models-v1")


def run_app(demo: str, model: str = "Random Forest") -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    by_label = {sb.label: sb for sb in at.sidebar.selectbox}
    by_label["Model"].select(model)
    by_label["Plik"].select(demo)  # opcje to nazwy plików (format_func)
    at.run()
    return at


def test_demo_files_present():
    assert {p.name for p in DEMO} >= {"darknet_tor_www_video.csv", "darknet_vpn_voip_video.csv"}


@pytest.mark.parametrize("demo", [p.name for p in DEMO])
def test_each_demo_file_gives_result(demo):
    at = run_app(demo)
    assert not at.exception and not at.error
    metrics = {m.label: m.value for m in at.metric}
    assert int(metrics["Sklasyfikowane"]) > 0 and "F1 (makro)" in metrics


def test_knn_shows_permutation_importance():
    at = run_app("darknet_tor_www_video.csv", model="k-NN")
    assert not at.exception and not at.error
    assert any("permutacyjna" in c.value for c in at.caption)
