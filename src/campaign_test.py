"""Test kampanii: czy RF odróżnia kampanię pomiarową na samym wideo z ruchu zwykłego.

    python src/campaign_test.py

Powrót do etapu 04 z etapu 08: wynik liczyły notebook EDA (13.10) i kontrola po /gate deep
(23.10, docs/decyzje.md, wpis E4), ale nie było go w reports/results/. Ten skrypt powtarza
tamten schemat (RF 200 drzew, class_weight="balanced", StratifiedGroupKFold 5 po sesjach,
ziarno 42, dokładność zbalansowana) dla każdego zestawu cech E4.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score

from experiments import FEATURE_SETS
from features import PROCESSED, load_flows
from model_store import file_sha256
from train import RESULTS, _git_state, git_provenance, resolve_features

OUT_NAME = "04_kampania"
SEED = 42
N_SPLITS = 5
N_ESTIMATORS = 200


def campaign_video(flows: pd.DataFrame) -> pd.DataFrame:
    """Wideo z ruchu zwykłego: jedyna usługa obecna w obu kampaniach bez tunelu."""
    return flows[(flows["service"] == "Video") & (flows["tunnel"] == "plain")]


def campaign_scores(video: pd.DataFrame, feature_sets: dict[str, list[str]], n_splits: int,
                    seed: int, n_estimators: int) -> pd.DataFrame:
    """Dokładność zbalansowana per fold; cel to kampania, grupy to sesje."""
    rows = []
    for name, columns in feature_sets.items():
        cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        rf = RandomForestClassifier(n_estimators=n_estimators, n_jobs=-1, random_state=seed,
                                    class_weight="balanced")
        scores = cross_val_score(rf, video[columns], video["campaign"], groups=video["session"],
                                 cv=cv, scoring="balanced_accuracy")
        rows += [{"feature_set": name, "n_features": len(columns), "fold": i,
                  "balanced_accuracy": s} for i, s in enumerate(scores)]
    return pd.DataFrame(rows)


def summary(folds: pd.DataFrame) -> pd.DataFrame:
    return (folds.groupby(["feature_set", "n_features"], sort=False)["balanced_accuracy"]
            .agg(["mean", "std"]).reset_index())


def markdown_table(summ: pd.DataFrame, video: pd.DataFrame) -> str:
    counts = video.groupby("campaign").agg(flows=("session", "size"),
                                           sessions=("session", "nunique"))
    lines = ["# Test kampanii: wideo z ruchu zwykłego, cel = kampania", "",
             "Wygenerowane przez `src/campaign_test.py`. RF, StratifiedGroupKFold "
             f"{N_SPLITS} po sesjach, dokładność zbalansowana (średnia ± odchylenie po foldach).",
             "", "| Kampania | Przepływy | Sesje |", "| --- | ---: | ---: |",
             *[f"| {c} | {r.flows} | {r.sessions} |" for c, r in counts.iterrows()],
             "", "| Zestaw cech | Cech | Dokładność zbalansowana |", "| --- | ---: | ---: |",
             *[f"| {r.feature_set} | {r.n_features} | {r.mean:.3f} ± {r.std:.3f} |"
               for r in summ.itertuples(index=False)]]
    return "\n".join(lines) + "\n"


def run_info(data_path: Path, feature_sets: dict[str, list[str]],
             git: dict[str, Any]) -> dict[str, Any]:
    return {"target": "campaign", "population": "Video, tunnel == plain", "groups": "session",
            "cv": {"kind": "StratifiedGroupKFold", "n_splits": N_SPLITS, "seed": SEED},
            "model": {"kind": "RandomForestClassifier", "n_estimators": N_ESTIMATORS,
                      "class_weight": "balanced"},
            "feature_sets": feature_sets,
            "data": {"path": data_path.name, "sha256": file_sha256(data_path)}, **git}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    ap.add_argument("--out", type=Path, default=RESULTS)
    args = ap.parse_args(argv)

    git_before = _git_state()
    video = campaign_video(load_flows(path=args.data))
    feature_sets = {name: resolve_features(name) for name in FEATURE_SETS}
    folds = campaign_scores(video, feature_sets, N_SPLITS, SEED, N_ESTIMATORS)
    git = git_provenance(git_before, _git_state())

    out_dir = args.out / OUT_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    table = markdown_table(summary(folds), video)
    folds.to_csv(out_dir / "folds.csv", index=False)
    (out_dir / "tabela.md").write_text(table, encoding="utf-8")
    (out_dir / "run.json").write_text(
        json.dumps(run_info(args.data, feature_sets, git), indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(table)
    print(f"Wyniki: {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
