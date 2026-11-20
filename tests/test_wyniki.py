import re
from pathlib import Path

import pandas as pd
import pytest

from make_figures_03b import E1, E2
from wyniki_dane import STEP_CLEAN, STEP_E1, STEP_E2, STEP_EXTERNAL, e6_paired, story_steps
from wyniki_tabele import _ordered

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
TABLES = ROOT / "reports" / "wyniki_tabele.md"
REPORT = ROOT / "reports" / "wyniki.md"


def _story_inputs() -> dict[str, pd.DataFrame]:
    e1e2 = pd.DataFrame({"task": "t", "model": "rf", "variant": [E1, E1, E2, E2, "E2 para IP"],
                         "f1_macro": [0.9, 1.0, 0.8, 0.8, 0.1]})
    e4 = pd.DataFrame({"task": "t", "model": "rf", "feature_set": ["bez_skrotow", "all"],
                       "split": "session", "f1_macro": [0.7, 0.2]})
    e7 = pd.DataFrame({"task": ["t"], "model": ["rf"], "f1_macro": [0.5],
                       "f1_macro_majority": [0.45]})
    return {"e1e2": e1e2, "e4": e4, "e7": e7}


def test_story_steps_takes_each_step_from_its_source() -> None:
    steps = story_steps(_story_inputs())
    rf = steps[steps["model"] == "rf"].set_index("step")["mean"]
    assert rf.to_dict() == pytest.approx({STEP_E1: 0.95, STEP_E2: 0.8, STEP_CLEAN: 0.7,
                                          STEP_EXTERNAL: 0.5})
    dummy = steps[steps["model"] == "dummy"]
    assert dummy["step"].tolist() == [STEP_EXTERNAL] and dummy["mean"].iloc[0] == 0.45


def test_e6_paired_subtracts_full_flow_within_fold() -> None:
    folds = pd.DataFrame({"population": "p", "model": "rf", "fold": [0, 1, 0, 1],
                          "n_first": [0, 0, 5, 5], "f1_macro": [0.9, 0.8, 0.95, 0.7]})
    row = e6_paired({"e6_folds": folds}).iloc[0]
    assert row["n_first"] == 5
    assert (row["mean"], row["min"], row["max"]) == pytest.approx((-0.025, -0.1, 0.05))


def test_ordered_uses_given_category_order_not_alphabet() -> None:
    df = pd.DataFrame({"model": ["rf", "dummy", "knn"], "v": [1, 2, 3]})
    assert _ordered(df, model=["dummy", "knn", "rf"])["v"].tolist() == [2, 3, 1]


def _snapshot(directory: Path) -> dict[str, tuple[int, int]]:
    return {str(p.relative_to(directory)): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in directory.rglob("*") if p.is_file()}


@pytest.mark.skipif(not (RESULTS / "e1e2_uslugi3_plain" / "predictions.parquet").exists(),
                    reason="T2 potrzebuje lokalnych predictions.parquet (komputer stacjonarny)")
def test_rerun_reproduces_tables_without_writing_results(tmp_path: Path) -> None:
    import make_figures_08

    before = _snapshot(RESULTS)
    make_figures_08.main(["--figures", str(tmp_path / "fig"),
                          "--tables", str(tmp_path / "wyniki_tabele.md")])
    assert _snapshot(RESULTS) == before
    assert (tmp_path / "wyniki_tabele.md").read_text(encoding="utf-8") == \
        TABLES.read_text(encoding="utf-8")
    expected = {p.name for p in (ROOT / "reports" / "figures").glob("1[6-7]_*.png")}
    assert expected <= {p.name for p in (tmp_path / "fig").glob("*.png")}
    assert len(list((tmp_path / "fig" / "slajdy").glob("S*.png"))) == 5


# całe liczby z przecinkiem dziesiętnym (0,957, 29,1); liczby całkowite i procenty bez części
# ułamkowej (51%, 62 przepływy) nie są sprawdzane
DECIMAL = re.compile(r"(?<![\d,])\d+,\d+(?![\d,])")


def test_every_decimal_in_report_comes_from_tables() -> None:
    tables = set(DECIMAL.findall(TABLES.read_text(encoding="utf-8")))
    numbers = set(DECIMAL.findall(REPORT.read_text(encoding="utf-8")))
    missing = sorted(numbers - tables)
    assert not missing, f"Liczby z wyniki.md bez źródła w wyniki_tabele.md: {missing}"
