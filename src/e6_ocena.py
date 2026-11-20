"""E6, sesja 2: VoIP vs Video z pierwszych N pakietów przepływu (etap 07, P4).

    python src/e6_ocena.py

Czyta data/external/iscx_e6/e6_prefiksy.parquet (`e6.py prefiksy`). Zadanie jak E2
`voip_video_vpncamp`: VoIP vs Video w kampanii VPN-nonVPN, oba tunele, warstwy usługa × tunel,
podział po sesjach (5 min), zestaw cech bez_skrotow, modele i schemat oceny z etapu 03a.
Dwie populacje (decyzja autora): wszystkie przepływy (krótsze niż N mają cechy z wszystkich
pakietów) i przepływy z co najmniej 20 pakietami (czysty efekt obcięcia). W populacji każdy
wariant N ma te same przepływy w tej samej kolejności, więc i te same foldy.
"""
import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import balanced_accuracy_score, f1_score

from e6 import E6_DIR, FIRST_N, FLOW_ID, FULL_FLOW, RESULTS
from evaluate import Prepared, SplitSpec, fold_metrics, run_cv
from models import get_model
from preprocess import assign_sessions
from train import _git_state, git_provenance
from usbvpn import FEATURES

CLASSES = ("VoIP", "Video")
MODELS = ("dummy", "knn", "tree", "rf")
SESSION_GAP_MIN = 5.0
METRICS = ["f1_macro", "balanced_accuracy", "f1_macro_session_weighted"]


@dataclass(frozen=True)
class Population:
    name: str
    min_packets: int
    first_n: tuple[int, ...]  # pełny przepływ (FULL_FLOW) dochodzi zawsze
    n_outer: int


# min20: największa sesja VoIP ma 33,5% klasy, przy 3 foldach każdy fold ma 12–14 sesji VoIP;
# w całej populacji 16% i przy 5 foldach co najmniej 7 sesji VoIP w foldzie (sprawdzone 20.11)
POPULATIONS = (Population("wszystkie", 0, FIRST_N, 5),
               Population("min20", 20, tuple(n for n in FIRST_N if n <= 20), 3))


def with_sessions(prefixes: pd.DataFrame, gap_min: float = SESSION_GAP_MIN) -> pd.DataFrame:
    """Sesje jak w preprocess.py; wiersze tego samego przepływu (różne N) mają tę samą sesję."""
    ts = pd.to_datetime(prefixes["ts_us"], unit="us")
    return prefixes.assign(ts=ts, session=assign_sessions(prefixes.assign(ts=ts), gap_min))


def variant_frame(prefixes: pd.DataFrame, pop: Population, n_first: int) -> pd.DataFrame:
    """Przepływy populacji z cechami jednego wariantu, w stałej kolejności klucza przepływu."""
    df = prefixes[(prefixes["n_first"] == n_first) & (prefixes["n_packets"] >= pop.min_packets)]
    if df.empty:
        raise ValueError(f"{pop.name}, N={n_first}: brak przepływów")
    return df.sort_values(FLOW_ID).reset_index(drop=True)


def prepared(df: pd.DataFrame) -> Prepared:
    everything = np.ones(len(df), dtype=bool)
    return Prepared(X=df[FEATURES], y=df["service"], groups=df["session"],
                    strata=df["service"] + "|" + df["traffic_type"],
                    train_mask=everything, test_mask=everything, classes=CLASSES)


def evaluate_variant(df: pd.DataFrame, pop: Population, n_first: int, models: tuple[str, ...],
                     seed: int, n_jobs: int) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    """Wiersze foldów (metryki, macierz pomyłek) i predykcje spoza foldu dla wszystkich modeli."""
    data = prepared(df)
    session_sizes = data.groups.value_counts()
    spec = SplitSpec("session", pop.n_outer, seed=seed)
    rows, preds = [], []
    for model in models:
        for out in run_cv(data, get_model(model), spec, n_jobs):
            y_true = data.y.iloc[out.test_idx]
            metrics = fold_metrics(y_true, out.y_pred, data.groups.iloc[out.test_idx], CLASSES,
                                   session_sizes)
            rows.append({"population": pop.name, "n_first": n_first, "model": model,
                         "fold": out.fold, **metrics,
                         "balanced_accuracy": balanced_accuracy_score(y_true, out.y_pred),
                         "confusion": json.dumps(metrics["confusion"]),  # wiersze/kolumny: CLASSES
                         "n_train_flows": len(out.train_idx),
                         "best_params": json.dumps(out.best_params, sort_keys=True, default=str)})
            preds.append(pd.DataFrame({"population": pop.name, "n_first": n_first, "model": model,
                                       "fold": out.fold, "row": out.test_idx,
                                       "y_true": y_true.to_numpy(), "y_pred": out.y_pred}))
    return rows, pd.concat(preds, ignore_index=True)


def summarize(folds: pd.DataFrame, preds: pd.DataFrame) -> pd.DataFrame:
    """Średnia i odchylenie po foldach oraz F1 makro i dokładność zbalansowana z predykcji OOF."""
    keys = ["population", "n_first", "model"]
    stats = folds.groupby(keys)[METRICS].agg(["mean", "std"])
    stats.columns = [f"{m}_{s}" for m, s in stats.columns]
    oof = preds.groupby(keys).apply(lambda g: pd.Series({
        "f1_macro_oof": f1_score(g["y_true"], g["y_pred"], labels=list(CLASSES),
                                 average="macro", zero_division=0),
        "balanced_accuracy_oof": balanced_accuracy_score(g["y_true"], g["y_pred"])}),
        include_groups=False)
    n_folds = folds.groupby(keys).size().rename("n_folds")
    return pd.concat([stats, oof, n_folds], axis=1).reset_index()


def population_counts(prefixes: pd.DataFrame) -> pd.DataFrame:
    """Na populację i klasę: przepływy, sesje i udział największej sesji w klasie."""
    rows = []
    for pop in POPULATIONS:
        df = variant_frame(prefixes, pop, FULL_FLOW)
        for svc, g in df.groupby("service"):
            sizes = g["session"].value_counts()
            rows.append({"populacja": pop.name, "usługa": svc, "przepływy": len(g),
                         "sesje": len(sizes), "największa sesja": round(sizes.iloc[0] / len(g), 3),
                         "foldy": pop.n_outer})
    return pd.DataFrame(rows)


def n_label(n_first: int) -> str:
    return "pełny" if n_first == FULL_FLOW else str(n_first)


def markdown_report(summary: pd.DataFrame, counts: pd.DataFrame) -> str:
    lines = ["# E6: VoIP vs Video z pierwszych N pakietów (kampania VPN-nonVPN)", "",
             "Wygenerowane przez `src/e6_ocena.py`. Podział po sesjach, zestaw bez_skrotow; "
             "średnia ± odchylenie po foldach, OOF: z predykcji spoza foldu.", "",
             counts.to_markdown(index=False), ""]
    for pop in POPULATIONS:
        part = summary[summary["population"] == pop.name]
        lines += [f"## Populacja {pop.name}", "",
                  "| Model | N | F1 makro | Dokładność zbalansowana | F1 ważone sesjami | "
                  "F1 makro OOF |", "| --- | --- | ---: | ---: | ---: | ---: |"]
        for r in part.sort_values(["model", "n_first"], key=_full_last).itertuples(index=False):
            lines.append(f"| {r.model} | {n_label(r.n_first)} | {r.f1_macro_mean:.3f} ± "
                         f"{r.f1_macro_std:.3f} | {r.balanced_accuracy_mean:.3f} ± "
                         f"{r.balanced_accuracy_std:.3f} | {r.f1_macro_session_weighted_mean:.3f} |"
                         f" {r.f1_macro_oof:.3f} |")
        lines.append("")
    return "\n".join(lines)


def _full_last(col: pd.Series) -> pd.Series:
    """Sortowanie: pełny przepływ po wszystkich N."""
    return col.replace(FULL_FLOW, np.iinfo(np.int64).max) if col.name == "n_first" else col


def run_info(data_path: Path, prefixes: pd.DataFrame, models: tuple[str, ...], seed: int,
             git: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": {"classes": list(CLASSES), "campaign": "vpn-nonvpn",
                 "stratify_by": ["service", "traffic_type"], "split": "session",
                 "session_gap_min": SESSION_GAP_MIN},
        "populations": [asdict(p) for p in POPULATIONS], "models": list(models), "seed": seed,
        "features": FEATURES,
        "data": {"path": data_path.name,
                 "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
                 "n_flows": int(prefixes[FLOW_ID].drop_duplicates().shape[0])},
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__},
        **git,
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=E6_DIR / "e6_prefiksy.parquet")
    ap.add_argument("--out", type=Path, default=RESULTS / "ocena")
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-jobs", type=int, default=-1)
    args = ap.parse_args(argv)

    git_before = _git_state()
    prefixes = with_sessions(pd.read_parquet(args.data))
    models = tuple(args.models)
    rows, preds = [], []
    for pop in POPULATIONS:
        for n_first in (*pop.first_n, FULL_FLOW):
            r, p = evaluate_variant(variant_frame(prefixes, pop, n_first), pop, n_first, models,
                                    args.seed, args.n_jobs)
            rows += r
            preds.append(p)
            print(f"{pop.name} N={n_label(n_first)}: gotowe", flush=True)
    folds, preds = pd.DataFrame(rows), pd.concat(preds, ignore_index=True)
    git = git_provenance(git_before, _git_state())
    summary = summarize(folds, preds)
    counts = population_counts(prefixes)

    args.out.mkdir(parents=True, exist_ok=True)
    folds.to_csv(args.out / "folds.csv", index=False)
    summary.to_csv(args.out / "summary.csv", index=False)
    preds.to_parquet(args.out / "predictions.parquet", index=False)
    text = markdown_report(summary, counts)
    (args.out / "e6_tabela.md").write_text(text, encoding="utf-8")
    (args.out / "run.json").write_text(
        json.dumps(run_info(args.data, prefixes, models, args.seed, git), indent=2,
                   ensure_ascii=False), encoding="utf-8")
    print(text)
    print(f"Wyniki: {args.out}")


if __name__ == "__main__":
    sys.exit(main())
