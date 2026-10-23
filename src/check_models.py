"""Kontrola potoków z Release models-v1: wczytanie i predykcja na sesjach odłożonych na pokaz.

    gh release download models-v1 -D models --skip-existing
    python src/check_models.py

Każde ostrzeżenie (np. o innej wersji scikit-learn) przerywa kontrolę błędem.
"""
import argparse
import sys
import warnings
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from experiments import TASKS
from features import PROCESSED, load_flows
from finalize import holdout_mask, keys_from_records
from model_store import MODELS_DIR, check_data, check_versions, load_metadata, load_pipeline
from train import task_frame


def holdout_flows(flows: pd.DataFrame, metadata: dict[str, Any], task: str) -> pd.DataFrame:
    """Przepływy odłożonych sesji należące do populacji zadania."""
    held = flows[holdout_mask(flows, keys_from_records(metadata["holdout"]["sessions"]))]
    df, _, test_mask = task_frame(held, TASKS[task])
    return df[test_mask]


def check_pipelines(flows: pd.DataFrame, metadata: dict[str, Any],
                    models_dir: Path) -> pd.DataFrame:
    rows = []
    for entry in metadata["pipelines"]:
        held = holdout_flows(flows, metadata, entry["task"])
        pipeline = load_pipeline(entry, models_dir)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            y_pred = pipeline.predict(held[metadata["features"]])
        rows.append({"task": entry["task"], "model": entry["model"], "n_flows": len(held),
                     "n_sessions": held["session"].nunique(),
                     "f1_macro": f1_score(held["service"], y_pred, labels=entry["classes"],
                                          average="macro", zero_division=0),
                     "accuracy": accuracy_score(held["service"], y_pred)})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    ap.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    args = ap.parse_args(argv)

    metadata = load_metadata(args.models_dir)
    check_versions(metadata)
    check_data(args.data, metadata)
    result = check_pipelines(load_flows(path=args.data), metadata, args.models_dir)
    print(result.round(3).to_string(index=False))
    print(f"OK: {len(result)} potoków wczytanych i sprawdzonych na sesjach odłożonych "
          "(wynik orientacyjny; raportowany wynik to CV z etapu 04)")


if __name__ == "__main__":
    sys.exit(main())
