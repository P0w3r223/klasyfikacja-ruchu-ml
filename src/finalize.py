"""Modele finalne (etap 05): sesje odłożone na pokaz, potoki i models/metadata.json.

    python src/finalize.py

Potoki uczone są na całej populacji zadania bez sesji odłożonych na pokaz, a hiperparametry
wybiera wewnętrzna CV po sesjach (fit_tuned). Raportowany wynik pochodzi z CV w etapie 04
(e4_bez_skrotow_*), nie z odłożonych sesji (docs/decyzje.md).
"""
import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from evaluate import SplitSpec, fit_tuned
from experiments import TASKS
from features import PROCESSED, built_session_gap_min, load_flows
from model_store import METADATA_FILE, MODELS_DIR, file_sha256, library_versions
from models import get_model
from preprocess import ip_pair
from train import RESULTS, _git_state, git_provenance, prepare, resolve_features

FINAL_TASKS = ("www_video_tor", "voip_video_vpncamp", "uslugi3_plain")
FINAL_MODELS = ("knn", "tree", "rf")
FINAL_FEATURE_SET = "bez_skrotow"
DATA_RELEASE = "data-processed-v1"
MODELS_RELEASE = "models-v1"
# opisy dla aplikacji (decyzja autora, etap 05)
TASK_INFO = {
    "www_video_tor": {
        "title": "WWW vs Video (kampania Tor-nonTor)", "role": "główne",
        "description": "Obie klasy z tej samej kampanii nagrań, więc model nie może ich "
                       "odróżnić po kampanii; uczciwa miara."},
    "voip_video_vpncamp": {
        "title": "VoIP vs Video (kampania VPN-nonVPN, ruch zwykły i VPN)", "role": "główne",
        "description": "Obie klasy z tej samej kampanii nagrań; model widział ruch zwykły "
                       "i ruch wewnątrz tunelu VPN."},
    "uslugi3_plain": {
        "title": "WWW / VoIP / Video (ruch zwykły)", "role": "odniesienie",
        "description": "Wynik zawyżony przez efekt kampanii: część Video model rozpoznaje "
                       "po kampanii nagrań, a nie po usłudze."},
}
# kolumny filtra ruchu tła (preprocess.background_reason); Protocol jest też cechą
FILTER_COLUMNS = ("Protocol", "Src Port", "Dst Port", "Dst IP")
HOLDOUT_STRATA = ["service", "campaign", "tunnel"]
KEY_COLUMNS = ["traffic_type", "service", "campaign", "tunnel", "ip_a", "ip_b",
               "ts_min", "ts_max", "n_flows"]
TS_FORMAT = "%Y-%m-%d %H:%M:%S"
# podział i ziarno strojenia; ziarno trafia też do drzewa i RF (models.ModelSpec.pipeline)
FINAL_SPLIT = SplitSpec("session")
# jak dopasować klucz sesji w surowym Darknet.CSV (etap 09)
KEY_MATCH_RULES = {
    "ip_pair": "ip_a i ip_b to mniejszy i większy adres w porównaniu tekstowym "
               "(preprocess.ip_pair), niezależnie od kierunku przepływu",
    "service": "po ujednoliceniu pisowni Label.1 przez preprocess.SERVICE_MAP",
    "traffic_type": "kolumna Label bez zmian",
    "ts": "Timestamp z Darknet.CSV (%d/%m/%Y %I:%M:%S %p), okno [ts_min, ts_max] włącznie",
    "n_flows": "liczone po filtrze ruchu tła, usunięciu wierszy z inf/NaN i duplikatów "
               "(preprocess.build); w surowym CSV to samo okno może mieć więcej wierszy",
}


@dataclass(frozen=True)
class HoldoutRule:
    """Ile sesji odłożyć w każdej grupie usługa × kampania × tunel i jakich rozmiarów.

    max_share: odłożona sesja ma mniej niż ten udział przepływów grupy, więc duże rozmowy
    VoIP (do 30% przepływów VoIP) zostają w treningu.
    """
    per_group: int = 2
    min_flows: int = 5
    max_share: float = 0.10
    seed: int = 42


@dataclass(frozen=True)
class FinalModel:
    task: str
    model: str
    pipeline: Pipeline
    best_params: dict[str, Any]
    inner_f1: float
    train_flows_per_class: dict[str, int]
    n_train_sessions: int
    search_s: float


def session_keys(flows: pd.DataFrame) -> pd.DataFrame:
    """Trwały klucz sesji: etykiety, nieuporządkowana para IP i zakres ts.

    Numer w kolumnie session zmienia się z wersją danych i progiem, a ten klucz da się
    dopasować także w surowym Darknet.CSV (etap 09).
    """
    pair = ip_pair(flows).str.split("|", expand=True)
    return (flows.assign(ip_a=pair[0], ip_b=pair[1])
            .groupby("session", sort=True)
            .agg(traffic_type=("traffic_type", "first"), service=("service", "first"),
                 campaign=("campaign", "first"), tunnel=("tunnel", "first"),
                 ip_a=("ip_a", "first"), ip_b=("ip_b", "first"),
                 ts_min=("ts", "min"), ts_max=("ts", "max"), n_flows=("ts", "size"))
            .reset_index())


def select_holdout(flows: pd.DataFrame, rule: HoldoutRule) -> pd.DataFrame:
    """Losuje rule.per_group sesji w każdej grupie usługa × kampania × tunel."""
    keys = session_keys(flows)
    group_total = keys.groupby(HOLDOUT_STRATA)["n_flows"].transform("sum")
    eligible = keys[(keys["n_flows"] >= rule.min_flows)
                    & (keys["n_flows"] < rule.max_share * group_total)]
    all_groups = keys.groupby(HOLDOUT_STRATA).size().index
    counts = eligible.groupby(HOLDOUT_STRATA).size().reindex(all_groups, fill_value=0)
    short = counts[counts < rule.per_group]
    if not short.empty:
        raise ValueError(f"Za mało sesji do odłożenia w grupach {short.to_dict()} "
                         f"(wymagane {rule.per_group}); zmień HoldoutRule")
    picked = pd.concat([g.sample(n=rule.per_group, random_state=rule.seed)
                        for _, g in eligible.groupby(HOLDOUT_STRATA)])
    return picked.sort_values(HOLDOUT_STRATA + ["ts_min"])[KEY_COLUMNS].reset_index(drop=True)


def holdout_mask(flows: pd.DataFrame, keys: pd.DataFrame) -> np.ndarray:
    """Przepływy odłożonych sesji; każdy klucz musi trafić dokładnie w n_flows przepływów."""
    pair = ip_pair(flows)
    mask = np.zeros(len(flows), dtype=bool)
    for key in keys.itertuples(index=False):
        hit = ((flows["traffic_type"] == key.traffic_type) & (flows["service"] == key.service)
               & (pair == f"{key.ip_a}|{key.ip_b}")
               & flows["ts"].between(key.ts_min, key.ts_max)).to_numpy()
        if hit.sum() != key.n_flows:
            raise ValueError(f"Klucz sesji {key._asdict()} wybiera {hit.sum()} przepływów "
                             f"zamiast {key.n_flows}; inne dane niż przy wyborze sesji?")
        mask |= hit
    return mask


def keys_to_records(keys: pd.DataFrame) -> list[dict[str, Any]]:
    return [{**row, "ts_min": row["ts_min"].strftime(TS_FORMAT),
             "ts_max": row["ts_max"].strftime(TS_FORMAT), "n_flows": int(row["n_flows"])}
            for row in keys.to_dict(orient="records")]


def keys_from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    keys = pd.DataFrame(records, columns=KEY_COLUMNS)
    return keys.assign(ts_min=pd.to_datetime(keys["ts_min"], format=TS_FORMAT),
                       ts_max=pd.to_datetime(keys["ts_max"], format=TS_FORMAT))


def fit_final(train_flows: pd.DataFrame, task: str, model: str, features: list[str],
              gap_min: float, n_jobs: int = -1) -> FinalModel:
    """Strojenie i dopasowanie na całej populacji zadania (bez odłożonych sesji)."""
    data = prepare(train_flows, TASKS[task], features, gap_min, built_gap_min=gap_min)
    train_idx = np.flatnonzero(data.train_mask)
    pipeline, params, inner_f1, _, search_s = fit_tuned(
        data, train_idx, get_model(model), FINAL_SPLIT, n_jobs)
    y = data.y.iloc[train_idx]
    # typy numpy zapisałyby się w JSON jako napisy albo przerwały zapis
    params = {k: v.item() if isinstance(v, np.generic) else v for k, v in params.items()}
    return FinalModel(task, model, pipeline, params, inner_f1,
                      {c: int((y == c).sum()) for c in data.classes},
                      int(data.groups.iloc[train_idx].nunique()), search_s)


def reported_cv(results_dir: Path, task: str) -> dict[str, dict[str, Any]]:
    """Wynik CV po sesjach z etapu 04 dla każdego modelu finalnego."""
    experiment = f"e4_{FINAL_FEATURE_SET}_{task}"
    path = results_dir / experiment / "summary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Brak {path}: metadata.json odsyła do wyniku CV z etapu 04")
    rows = pd.read_csv(path).query("split == 'session'").set_index("model")
    return {m: {"experiment": experiment, "f1_macro_mean": float(rows.at[m, "f1_macro_mean"]),
                "f1_macro_std": float(rows.at[m, "f1_macro_std"])} for m in FINAL_MODELS}


def pipeline_entry(fm: FinalModel, path: Path, cv: dict[str, Any]) -> dict[str, Any]:
    return {"task": fm.task, "model": fm.model, "classes": list(TASKS[fm.task].classes),
            "file": path.name, "sha256": file_sha256(path), "best_params": fm.best_params,
            "fit_seed": FINAL_SPLIT.seed, "inner_cv_folds": FINAL_SPLIT.n_inner,
            "inner_cv_f1_macro": fm.inner_f1, "train_flows_per_class": fm.train_flows_per_class,
            "n_train_sessions": fm.n_train_sessions, "search_s": round(fm.search_s, 1),
            "reported_cv": cv}


def build_metadata(entries: list[dict[str, Any]], features: list[str], keys: pd.DataFrame,
                   rule: HoldoutRule, data: dict[str, Any], git: dict[str, Any]) -> dict[str, Any]:
    """Kontrakt potoków z aplikacją (etap 09) i z E7."""
    return {
        "models_release": MODELS_RELEASE,
        "tasks": {t: {**TASK_INFO[t], "classes": list(TASKS[t].classes)} for t in FINAL_TASKS},
        "feature_set": FINAL_FEATURE_SET,
        "features": features,
        "input_columns": list(dict.fromkeys([*FILTER_COLUMNS, *features])),
        "filter_columns": list(FILTER_COLUMNS),
        # Label.1 w surowym CSV; pisownia ujednolicana przez preprocess.SERVICE_MAP
        "label_column": "Label.1",
        "data": data,
        "holdout": {"rule": asdict(rule), "ts_format": TS_FORMAT,
                    "match_rules": KEY_MATCH_RULES, "sessions": keys_to_records(keys)},
        "versions": library_versions(),
        "git": git,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pipelines": entries,
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    ap.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--min-flows", type=int, default=HoldoutRule.min_flows)
    ap.add_argument("--max-share", type=float, default=HoldoutRule.max_share)
    ap.add_argument("--n-jobs", type=int, default=-1)
    args = ap.parse_args(argv)

    rule = HoldoutRule(min_flows=args.min_flows, max_share=args.max_share)
    flows = load_flows(path=args.data)
    gap_min = built_session_gap_min(args.data.with_name("features.json"))
    keys = select_holdout(flows, rule)
    train_flows = flows[~holdout_mask(flows, keys)]
    features = resolve_features(FINAL_FEATURE_SET)
    # przed treningiem: brak wyniku E4 nie może wyjść dopiero po kilku minutach
    cv = {task: reported_cv(args.results, task) for task in FINAL_TASKS}
    git_before = _git_state()
    args.models_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for task in FINAL_TASKS:
        for model in FINAL_MODELS:
            fm = fit_final(train_flows, task, model, features, gap_min, args.n_jobs)
            path = args.models_dir / f"{task}__{model}.joblib"
            joblib.dump(fm.pipeline, path, compress=3)
            entries.append(pipeline_entry(fm, path, cv[task][model]))
            print(f"{task}/{model}: F1 wewn. CV {fm.inner_f1:.3f}, {fm.best_params}, "
                  f"{fm.search_s:.0f} s")
    data = {"release": DATA_RELEASE, "file": args.data.name,
            "sha256": file_sha256(args.data), "n_flows": len(flows), "session_gap_min": gap_min}
    metadata = build_metadata(entries, features, keys, rule, data,
                              git_provenance(git_before, _git_state()))
    (args.models_dir / METADATA_FILE).write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Odłożone sesje: {len(keys)} ({int(keys['n_flows'].sum())} przepływów); "
          f"potoki i {METADATA_FILE}: {args.models_dir}")


if __name__ == "__main__":
    sys.exit(main())
