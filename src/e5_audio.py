"""E5: przepływy Audio przez finalne potoki 3-klasowe (etap 05).

    python src/e5_audio.py

Model 3-klasowy uczono tylko na ruchu zwykłym, a Audio jest w obu kampaniach i w VPN,
więc rozkład przewidzianych klas rozbijamy na kampanię i tunel. Poza przepływami liczymy
też sesje (klasa większości w sesji), bo kilka dużych sesji dominuje liczby przepływów.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from features import PROCESSED, load_flows
from model_store import (MODELS_DIR, check_versions, file_sha256, find_pipeline, load_metadata,
                         load_pipeline)
from train import RESULTS, _git_state, git_provenance

TASK = "uslugi3_plain"
OUT_NAME = "05_e5"
SPLIT_BY = ["campaign", "tunnel"]


def predict_audio(audio: pd.DataFrame, pipelines: dict[str, Pipeline],
                  features: list[str]) -> pd.DataFrame:
    return pd.concat([audio[SPLIT_BY + ["session"]].assign(model=name,
                                                           y_pred=p.predict(audio[features]))
                      for name, p in pipelines.items()], ignore_index=True)


def _shares(df: pd.DataFrame, classes: list[str], unit: str) -> pd.DataFrame:
    counts = (df.groupby(["model", *SPLIT_BY])["y_pred"].value_counts()
              .unstack(fill_value=0).reindex(columns=classes, fill_value=0))
    total = counts.sum(axis=1)
    shares = counts.div(total, axis=0).add_prefix("share_")
    return pd.concat([counts.add_prefix("n_"), shares], axis=1).assign(
        unit=unit, total=total).reset_index()


def distribution(preds: pd.DataFrame, classes: list[str]) -> pd.DataFrame:
    """Rozkład klas per model × kampania × tunel: dla przepływów i dla sesji (większość)."""
    majority = (preds.groupby(["model", *SPLIT_BY, "session"])["y_pred"]
                .agg(lambda s: s.value_counts().index[0]).reset_index())
    return pd.concat([_shares(preds, classes, "flows"), _shares(majority, classes, "sessions")],
                     ignore_index=True)


def markdown_table(dist: pd.DataFrame, classes: list[str]) -> str:
    lines = ["| Model | Kampania | Tunel | Jednostka | Liczba | "
             + " | ".join(f"% {c}" for c in classes) + " |",
             "| --- | --- | --- | --- | ---: | " + " | ".join("---:" for _ in classes) + " |"]
    for r in dist.sort_values(["model", *SPLIT_BY, "unit"]).itertuples(index=False):
        row = r._asdict()
        shares = " | ".join(f"{100 * row[f'share_{c}']:.1f}" for c in classes)
        unit = "przepływy" if r.unit == "flows" else "sesje"
        lines.append(f"| {r.model} | {r.campaign} | {r.tunnel} | {unit} | {r.total} | {shares} |")
    return "\n".join(lines) + "\n"


def run_info(metadata: dict[str, Any], data_path: Path, git: dict[str, Any]) -> dict[str, Any]:
    return {"task": TASK, "models_release": metadata["models_release"],
            "pipelines": {e["model"]: e["sha256"] for e in metadata["pipelines"]
                          if e["task"] == TASK},
            "data": {"path": data_path.name, "sha256": file_sha256(data_path)}, **git}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    ap.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    ap.add_argument("--out", type=Path, default=RESULTS)
    args = ap.parse_args(argv)

    metadata = load_metadata(args.models_dir)
    check_versions(metadata)
    models = [e["model"] for e in metadata["pipelines"] if e["task"] == TASK]
    pipelines = {m: load_pipeline(find_pipeline(metadata, TASK, m), args.models_dir)
                 for m in models}
    classes = metadata["tasks"][TASK]["classes"]
    git_before = _git_state()
    flows = load_flows(include_audio=True, path=args.data)
    preds = predict_audio(flows[flows["service"] == "Audio"], pipelines, metadata["features"])
    dist = distribution(preds, classes)
    git = git_provenance(git_before, _git_state())

    out_dir = args.out / OUT_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    dist.to_csv(out_dir / "distribution.csv", index=False)
    (out_dir / "e5_tabela.md").write_text(
        f"# E5: Audio przez potoki {TASK}\n\n{markdown_table(dist, classes)}", encoding="utf-8")
    (out_dir / "run.json").write_text(
        json.dumps(run_info(metadata, args.data, git), indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(markdown_table(dist, classes))
    print(f"Wyniki: {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
