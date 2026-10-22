"""Uruchamia eksperyment z rejestru (experiments.py) i zapisuje wyniki do reports/results/.

    python src/train.py --experiment pilot_03a
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import f1_score

from evaluate import FoldOutcome, Prepared, SplitSpec, fold_metrics, run_cv
from experiments import FEATURE_SETS, TASKS, Experiment, Filter, Task, get_experiment
from features import PROCESSED, feature_list, load_flows
from models import get_model
from preprocess import assign_sessions

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
# próg, z którym preprocess.py zbudował kolumnę session w flows.parquet
BUILT_GAP_MIN = 5.0
SUMMARY_METRICS = ["f1_macro", "f1_macro_session_weighted", "accuracy"]


@dataclass(frozen=True)
class ExperimentResult:
    folds: pd.DataFrame
    predictions: pd.DataFrame
    confusion: dict[str, Any]


def _matches(df: pd.DataFrame, flt: Filter) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col, values in flt.items():
        mask &= df[col].isin(values)
    return mask


def resolve_features(name: str) -> list[str]:
    if name not in FEATURE_SETS:
        raise KeyError(f"Nieznany zestaw cech {name!r}; dostępne: {sorted(FEATURE_SETS)}")
    return FEATURE_SETS[name](feature_list())


def prepare(flows: pd.DataFrame, task: Task, features: list[str], gap_min: float) -> Prepared:
    """Wybiera populację zadania; przy innym progu sesji przelicza je w pamięci."""
    if gap_min != BUILT_GAP_MIN:
        flows = flows.assign(session=assign_sessions(flows, gap_min))
    in_classes = flows["service"].isin(task.classes)
    train = in_classes & _matches(flows, task.train)
    test = in_classes & _matches(flows, task.test or task.train)
    df = flows[train | test].reset_index(drop=True)
    if df.empty:
        raise ValueError(f"Zadanie {task.name}: filtr nie wybrał żadnego przepływu")
    return Prepared(
        X=df[features], y=df["service"], groups=df["session"],
        strata=df[list(task.stratify_by)].astype(str).agg("|".join, axis=1),
        train_mask=train[train | test].to_numpy(), test_mask=test[train | test].to_numpy(),
        classes=task.classes,
    )


def _fold_row(exp: Experiment, model: str, split: str, out: FoldOutcome,
              metrics: dict[str, Any]) -> dict[str, Any]:
    return {"experiment": exp.name, "task": exp.task, "model": model, "split": split,
            "repeat": out.repeat, "fold": out.fold, **metrics,
            "n_train_flows": len(out.train_idx), "inner_best_f1": out.inner_best_f1,
            "best_params": json.dumps(out.best_params, sort_keys=True, default=str),
            "fit_s": out.fit_s, "search_s": out.search_s, "predict_s": out.predict_s}


def run_experiment(exp: Experiment, flows: pd.DataFrame, n_jobs: int = -1) -> ExperimentResult:
    data = prepare(flows, TASKS[exp.task], resolve_features(exp.feature_set),
                   exp.session_gap_min)
    rows, preds, confusion = [], [], {}
    for model in exp.models:
        for split in exp.splits:
            spec = SplitSpec(split, exp.n_outer, exp.n_inner, exp.n_repeats, exp.seed)
            per_fold = []
            for out in run_cv(data, get_model(model), spec, n_jobs):
                metrics = fold_metrics(data.y.iloc[out.test_idx], out.y_pred,
                                       data.groups.iloc[out.test_idx], data.classes)
                per_fold.append(metrics.pop("confusion"))
                rows.append(_fold_row(exp, model, split, out, metrics))
                preds.append(pd.DataFrame({
                    "model": model, "split": split, "repeat": out.repeat, "fold": out.fold,
                    "row": out.test_idx, "session": data.groups.iloc[out.test_idx].to_numpy(),
                    "y_true": data.y.iloc[out.test_idx].to_numpy(), "y_pred": out.y_pred}))
            confusion[f"{model}/{split}"] = {
                "classes": list(data.classes), "per_fold": per_fold,
                "total": np.sum(per_fold, axis=0).tolist()}
    return ExperimentResult(pd.DataFrame(rows), pd.concat(preds, ignore_index=True), confusion)


def summarize(result: ExperimentResult, classes: tuple[str, ...]) -> pd.DataFrame:
    """Średnia, odchylenie, min i max po foldach oraz F1 makro z predykcji spoza foldu (OOF)."""
    cols = SUMMARY_METRICS + [f"f1_{c}" for c in classes]
    stats = result.folds.groupby(["model", "split"])[cols].agg(["mean", "std", "min", "max"])
    stats.columns = [f"{m}_{s}" for m, s in stats.columns]
    oof = pd.Series({
        key: np.mean([f1_score(r["y_true"], r["y_pred"], labels=list(classes), average="macro",
                               zero_division=0) for _, r in g.groupby("repeat")])
        for key, g in result.predictions.groupby(["model", "split"])}, name="f1_macro_oof")
    oof.index.names = ["model", "split"]
    n_folds = result.folds.groupby(["model", "split"]).size().rename("n_folds")
    return pd.concat([stats, oof, n_folds], axis=1).reset_index()


def _git_state() -> dict[str, Any]:
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                               text=True, check=True).stdout.strip() != ""
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"commit": None, "dirty": None, "git_error": str(exc)}
    return {"commit": sha, "dirty": dirty}


def run_info(exp: Experiment, data_path: Path, flows: pd.DataFrame) -> dict[str, Any]:
    return {
        "experiment": asdict(exp), "task": asdict(TASKS[exp.task]),
        "features": resolve_features(exp.feature_set),
        "data": {"path": data_path.name,
                 "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
                 "n_flows": len(flows)},
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__},
        **_git_state(),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def write_results(result: ExperimentResult, summary: pd.DataFrame, info: dict[str, Any],
                  out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    result.folds.to_csv(out_dir / "folds.csv", index=False)
    summary.to_csv(out_dir / "summary.csv", index=False)
    (out_dir / "confusion.json").write_text(json.dumps(result.confusion, indent=1),
                                            encoding="utf-8")
    (out_dir / "run.json").write_text(json.dumps(info, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    # predykcje OOF tylko lokalnie (*.parquet jest w .gitignore)
    result.predictions.to_parquet(out_dir / "predictions.parquet", index=False)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    ap.add_argument("--out", type=Path, default=RESULTS)
    ap.add_argument("--n-jobs", type=int, default=-1)
    args = ap.parse_args(argv)

    exp = get_experiment(args.experiment)
    flows = load_flows(path=args.data)
    result = run_experiment(exp, flows, args.n_jobs)
    summary = summarize(result, TASKS[exp.task].classes)
    write_results(result, summary, run_info(exp, args.data, flows), args.out / exp.name)
    cols = ["model", "split", "f1_macro_mean", "f1_macro_std", "f1_macro_min",
            "f1_macro_max", "f1_macro_oof"]
    print(summary[cols].round(3).to_string(index=False))
    print(f"Wyniki: {args.out / exp.name}")


if __name__ == "__main__":
    sys.exit(main())
