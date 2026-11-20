"""Dane do zestawienia wyników (etap 08): odczyt plików z reports/results/ i ich podsumowania.

Rysunki (`figures_08.py`) i tabele (`wyniki_tabele.py`) biorą liczby z tych samych funkcji,
więc slajd i tabela nie mogą się rozjechać. Moduł tylko czyta; niczego nie zapisuje.
"""
from pathlib import Path

import pandas as pd

from make_figures_03b import E1, E2

# klucz → plik w reports/results/; ścieżki trafiają też do tabel jako źródło liczb
SOURCES = {
    "e1e2": "03b_folds.csv",
    "e3": "04_e3_folds.csv",
    "e4": "04_e4_folds.csv",
    "e4_importance": "04_e4_importance.csv",
    "kampania": "04_kampania/folds.csv",
    "e5": "05_e5/distribution.csv",
    "e6": "07_e6/ocena/summary.csv",
    "e6_folds": "07_e6/ocena/folds.csv",
    "e7": "06_e7/ocena/metryki.csv",
}
TASKS = ["www_video_tor", "voip_video_vpncamp", "uslugi3_plain"]
TASK_SHORT = {"www_video_tor": "WWW vs Video", "voip_video_vpncamp": "VoIP vs Video",
              "uslugi3_plain": "3 usługi"}
MODELS = ["dummy", "knn", "tree", "rf"]
TRAINED = ["knn", "tree", "rf"]

# kroki osi opowieści: od podziału losowego do innego zbioru
STEP_E1, STEP_E2, STEP_CLEAN, STEP_EXTERNAL = (
    "E1: podział losowy", "E2: po sesjach", "bez skrótów", "USBVPN2022")
STEPS = [STEP_E1, STEP_E2, STEP_CLEAN, STEP_EXTERNAL]


def load_inputs(results: Path) -> dict[str, pd.DataFrame]:
    missing = [p for p in SOURCES.values() if not (results / p).exists()]
    if missing:
        raise FileNotFoundError(f"Brak plików wyników w {results}: {missing}; "
                                "brakującą liczbę liczy etap, który ją wytwarza")
    return {key: pd.read_csv(results / path) for key, path in SOURCES.items()}


def _mean_std(df: pd.DataFrame, keys: list[str], value: str = "f1_macro") -> pd.DataFrame:
    return (df.groupby(keys, sort=False)[value].agg(["mean", "std", "count"])
            .reset_index().rename(columns={"count": "n_folds"}))


def main_table(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """F1 makro: zadanie × model × (podział, zestaw cech); E1/E2 z 03b, reszta z E4."""
    e1e2 = inputs["e1e2"][inputs["e1e2"]["variant"].isin([E1, E2])].assign(
        variant=lambda d: d["variant"].map({E1: "E1 wszystkie", E2: "E2 wszystkie"}))
    e4 = inputs["e4"].query("feature_set in ['bez_idle', 'bez_skrotow']").assign(
        variant=lambda d: d["split"].map({"random": "E1", "session": "E2"})
        + " " + d["feature_set"])
    both = pd.concat([e1e2, e4], ignore_index=True)
    return _mean_std(both, ["task", "model", "variant"])


def story_steps(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """F1 makro na kolejnych krokach osi opowieści, dla każdego zadania i modelu."""
    e1e2 = _mean_std(inputs["e1e2"][inputs["e1e2"]["variant"].isin([E1, E2])],
                     ["task", "model", "variant"])
    e1e2["step"] = e1e2.pop("variant").map({E1: STEP_E1, E2: STEP_E2})
    clean = _mean_std(inputs["e4"].query("feature_set == 'bez_skrotow'"), ["task", "model"])
    e7 = inputs["e7"].rename(columns={"f1_macro": "mean"}).assign(std=float("nan"), n_folds=0)
    e7_dummy = inputs["e7"].drop_duplicates("task").assign(
        model="dummy", mean=lambda d: d["f1_macro_majority"], std=float("nan"), n_folds=0)
    cols = ["task", "model", "mean", "std", "n_folds", "step"]
    return pd.concat([e1e2[cols], clean.assign(step=STEP_CLEAN)[cols],
                      e7.assign(step=STEP_EXTERNAL)[cols],
                      e7_dummy.assign(step=STEP_EXTERNAL)[cols]], ignore_index=True)


def campaign_test(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return _mean_std(inputs["kampania"], ["feature_set", "n_features"], "balanced_accuracy")


def e3_summary(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return _mean_std(inputs["e3"], ["feature_set", "task", "model"])


def e4_summary(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return _mean_std(inputs["e4"].query("split == 'session'"), ["feature_set", "task", "model"])


def e4_importance(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Ważność permutacyjna grup (RF, po sesjach), średnia po foldach."""
    imp = inputs["e4_importance"].query("split == 'session'")
    return (imp.groupby(["feature_set", "task", "group"], sort=False)["perm_mean"].mean()
            .reset_index())


def e5_shares(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return inputs["e5"].query("unit == 'flows'").reset_index(drop=True)


def e6_curve(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return inputs["e6"].copy()


def e6_paired(inputs: dict[str, pd.DataFrame], full_flow: int = 0) -> pd.DataFrame:
    """Różnica F1 makro N − pełny przepływ, parami po foldach (te same przepływy i foldy)."""
    folds = inputs["e6_folds"]
    full = folds[folds["n_first"] == full_flow][["population", "model", "fold", "f1_macro"]]
    pairs = folds[folds["n_first"] != full_flow].merge(
        full, on=["population", "model", "fold"], suffixes=("", "_full"), validate="m:1")
    pairs["diff"] = pairs["f1_macro"] - pairs["f1_macro_full"]
    return (pairs.groupby(["population", "model", "n_first"])["diff"]
            .agg(["mean", "std", "min", "max"]).reset_index())


def e7_compare(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return inputs["e7"][["task", "model", "cv_f1_macro", "cv_f1_macro_std", "f1_macro",
                         "balanced_accuracy", "f1_macro_majority"]].copy()
