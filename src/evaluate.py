"""Schemat oceny: zagnieżdżona walidacja krzyżowa (docs/decyzje.md, etap 03a).

Foldy zewnętrzne dzielą populację testową; trening foldu to populacja
treningowa bez wierszy (podział losowy) albo sesji (podział po sesjach) foldu
testowego. Strojenie widzi tylko trening foldu. Moduł nie robi I/O i od etapu
03a się nie zmienia; kolejne eksperymenty zmieniają tylko konfigurację.
"""
import time
from dataclasses import dataclass
from typing import Any, Iterator, Literal

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline

from models import ModelSpec

Fold = tuple[np.ndarray, np.ndarray]


@dataclass(frozen=True)
class SplitSpec:
    kind: Literal["random", "session"]
    n_outer: int = 5
    n_inner: int = 3
    n_repeats: int = 1
    seed: int = 42
    min_test_groups_per_class: int = 2


@dataclass(frozen=True)
class Prepared:
    """Dane jednego zadania; maski wybierają populację treningową i testową."""
    X: pd.DataFrame
    y: pd.Series
    groups: pd.Series
    strata: pd.Series
    train_mask: np.ndarray
    test_mask: np.ndarray
    classes: tuple[str, ...]


@dataclass(frozen=True)
class FoldOutcome:
    repeat: int
    fold: int
    train_idx: np.ndarray
    test_idx: np.ndarray
    fitted: Pipeline
    y_pred: np.ndarray
    best_params: dict[str, Any]
    inner_best_f1: float
    fit_s: float
    search_s: float
    predict_s: float


def _split(kind: str, n_splits: int, seed: int, strata: pd.Series,
           groups: pd.Series) -> list[Fold]:
    """Foldy (pozycje względem strata); przy podziale po sesjach sesja nie jest dzielona."""
    if kind == "session":
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(splitter.split(strata, strata, groups))
    if kind == "random":
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(splitter.split(strata, strata))
    raise ValueError(f"Nieznany rodzaj podziału {kind!r}; dostępne: random, session")


def _check_groups_per_class(y: pd.Series, groups: pd.Series, classes: tuple[str, ...],
                            minimum: int, where: str) -> None:
    counts = groups.groupby(y).nunique().reindex(list(classes), fill_value=0)
    short = counts[counts < minimum]
    if not short.empty:
        raise ValueError(
            f"{where}: za mało sesji w klasach {short.to_dict()} (wymagane >= {minimum}); "
            "zmniejsz liczbę foldów albo zmień zadanie")


def outer_folds(data: Prepared, spec: SplitSpec, repeat: int) -> list[Fold]:
    """Pary (trening, test) jako pozycje wierszy w data.X."""
    test_pos = np.flatnonzero(data.test_mask)
    folds = []
    for _, fold_test in _split(spec.kind, spec.n_outer, spec.seed + repeat,
                               data.strata.iloc[test_pos], data.groups.iloc[test_pos]):
        test_idx = test_pos[fold_test]
        exclude = np.zeros(len(data.y), dtype=bool)
        if spec.kind == "session":
            exclude = data.groups.isin(data.groups.iloc[test_idx]).to_numpy(copy=True)
        exclude[test_idx] = True
        train_idx = np.flatnonzero(data.train_mask & ~exclude)
        folds.append((train_idx, test_idx))
    return folds


def inner_folds(data: Prepared, train_idx: np.ndarray, spec: SplitSpec) -> list[Fold]:
    """Foldy strojenia w obrębie treningu foldu zewnętrznego (pozycje względem train_idx)."""
    y, groups = data.y.iloc[train_idx], data.groups.iloc[train_idx]
    folds = _split(spec.kind, spec.n_inner, spec.seed, data.strata.iloc[train_idx], groups)
    for i, fold in enumerate(folds):
        for part, idx in zip(("trening", "walidacja"), fold):
            _check_groups_per_class(y.iloc[idx], groups.iloc[idx], data.classes, 1,
                                    f"fold wewnętrzny {i} ({part})")
    return folds


def fit_tuned(data: Prepared, train_idx: np.ndarray, model: ModelSpec, spec: SplitSpec,
              n_jobs: int = -1) -> tuple[Pipeline, dict[str, Any], float, float, float]:
    """Strojenie na train_idx i dopasowanie; tak samo powstaje model finalny (etap 05).

    Zwraca: potok, najlepsze parametry, F1 wewnętrznej CV, czas refitu, czas całości.
    """
    X, y = data.X.iloc[train_idx], data.y.iloc[train_idx]
    start = time.perf_counter()
    if not model.grid:
        fitted = model.pipeline(spec.seed).fit(X, y)
        elapsed = time.perf_counter() - start
        return fitted, {}, float("nan"), elapsed, elapsed
    search = GridSearchCV(model.pipeline(spec.seed), model.param_grid(), scoring="f1_macro",
                          cv=inner_folds(data, train_idx, spec), refit=True,
                          n_jobs=n_jobs, error_score="raise")
    search.fit(X, y)
    params = {k.removeprefix("clf__"): v for k, v in search.best_params_.items()}
    return (search.best_estimator_, params, float(search.best_score_),
            float(search.refit_time_), time.perf_counter() - start)


def run_cv(data: Prepared, model: ModelSpec, spec: SplitSpec,
           n_jobs: int = -1) -> Iterator[FoldOutcome]:
    for repeat in range(spec.n_repeats):
        for fold, (train_idx, test_idx) in enumerate(outer_folds(data, spec, repeat)):
            _check_groups_per_class(data.y.iloc[test_idx], data.groups.iloc[test_idx],
                                    data.classes, spec.min_test_groups_per_class,
                                    f"powtórzenie {repeat}, fold testowy {fold}")
            fitted, params, inner_f1, fit_s, search_s = fit_tuned(
                data, train_idx, model, spec, n_jobs)
            start = time.perf_counter()
            y_pred = fitted.predict(data.X.iloc[test_idx])
            predict_s = time.perf_counter() - start
            yield FoldOutcome(repeat, fold, train_idx, test_idx, fitted, y_pred, params,
                              inner_f1, fit_s, search_s, predict_s)


def fold_metrics(y_true: pd.Series, y_pred: np.ndarray, groups: pd.Series,
                 classes: tuple[str, ...],
                 session_sizes: pd.Series | None = None) -> dict[str, Any]:
    """Metryki jednego foldu i jego diagnostyka (liczności, udział największej sesji).

    session_sizes: rozmiary sesji w całej populacji testowej (wagi F1 ważonej sesjami).
    Bez nich liczone w foldzie, co przy podziale losowym daje rozmiar fragmentu sesji.
    """
    labels = list(classes)
    in_fold = groups.value_counts()
    sizes = groups.map(session_sizes if session_sizes is not None else in_fold).to_numpy()
    y_true, groups = y_true.to_numpy(), groups.to_numpy()
    per_class = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    out: dict[str, Any] = {
        "f1_macro": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        # każda sesja waży tyle samo: czy wynik nie ciągnie jedna długa rozmowa
        "f1_macro_session_weighted": f1_score(y_true, y_pred, labels=labels, average="macro",
                                              sample_weight=1.0 / sizes, zero_division=0),
        "largest_test_session_share": in_fold.max() / len(y_true),
    }
    for cls, f1 in zip(labels, per_class):
        mask = y_true == cls
        out[f"f1_{cls}"] = f1
        out[f"n_test_flows_{cls}"] = int(mask.sum())
        out[f"n_test_sessions_{cls}"] = int(pd.unique(groups[mask]).size)
        # w klasie z kilkoma sesjami (VoIP) jedna rozmowa potrafi zdominować fold
        out[f"largest_test_session_share_{cls}"] = (
            pd.Series(groups[mask]).value_counts().max() / mask.sum() if mask.any() else 0.0)
    out["confusion"] = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    return out
