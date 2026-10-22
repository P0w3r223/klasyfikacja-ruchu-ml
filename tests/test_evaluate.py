"""Testy schematu oceny (src/evaluate.py) na syntetycznych danych."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.pipeline import Pipeline

from evaluate import Prepared, SplitSpec, fold_metrics, outer_folds, run_cv
from models import ModelSpec, get_model

CLASSES = ("VoIP", "Video")


def make_data(sessions_per_class: int = 12, flows_per_session: int = 4,
              train_tunnels: tuple[str, ...] = ("plain", "vpn"),
              test_tunnels: tuple[str, ...] = ("plain", "vpn"), seed: int = 0) -> Prepared:
    """Sesje o nierównych rozmiarach; klasy dobrze rozdzielne na obu cechach."""
    rng = np.random.default_rng(seed)
    rows, session = [], 0
    for cls_i, cls in enumerate(CLASSES):
        for tunnel in ("plain", "vpn"):
            for k in range(sessions_per_class):
                for _ in range(flows_per_session + k % 3):
                    rows.append({"f1": rng.normal(3 * cls_i), "f2": rng.normal(-3 * cls_i),
                                 "service": cls, "tunnel": tunnel, "session": session})
                session += 1
    df = pd.DataFrame(rows)
    return Prepared(
        X=df[["f1", "f2"]], y=df["service"], groups=df["session"],
        strata=df["service"] + "|" + df["tunnel"],
        train_mask=df["tunnel"].isin(train_tunnels).to_numpy(),
        test_mask=df["tunnel"].isin(test_tunnels).to_numpy(), classes=CLASSES,
    )


@pytest.mark.parametrize("repeat", [0, 1])
def test_session_split_never_shares_a_session(repeat):
    data = make_data()
    for train_idx, test_idx in outer_folds(data, SplitSpec("session"), repeat):
        shared = set(data.groups.iloc[train_idx]) & set(data.groups.iloc[test_idx])
        assert not shared


@pytest.mark.parametrize("kind", ["session", "random"])
def test_every_test_row_is_tested_exactly_once(kind):
    data = make_data()
    folds = outer_folds(data, SplitSpec(kind), repeat=0)
    tested = np.concatenate([test for _, test in folds])
    assert len(folds) == 5
    assert sorted(tested) == list(np.flatnonzero(data.test_mask))
    for train_idx, test_idx in folds:
        assert not set(train_idx) & set(test_idx)


def test_random_split_keeps_rest_of_session_in_training():
    data = make_data()
    train_idx, test_idx = outer_folds(data, SplitSpec("random"), repeat=0)[0]
    assert set(data.groups.iloc[train_idx]) & set(data.groups.iloc[test_idx])


def test_repeats_change_the_split():
    data = make_data()
    spec = SplitSpec("session")
    first = [tuple(t) for _, t in outer_folds(data, spec, repeat=0)]
    second = [tuple(t) for _, t in outer_folds(data, spec, repeat=1)]
    assert first != second


def test_cross_population_uses_the_same_test_folds():
    plain_to_vpn = make_data(train_tunnels=("plain",), test_tunnels=("vpn",))
    vpn_to_vpn = make_data(train_tunnels=("vpn",), test_tunnels=("vpn",))
    spec = SplitSpec("session")
    cross = outer_folds(plain_to_vpn, spec, repeat=0)
    within = outer_folds(vpn_to_vpn, spec, repeat=0)
    for (cross_train, cross_test), (_, within_test) in zip(cross, within):
        assert list(cross_test) == list(within_test)
        assert list(cross_train) == list(np.flatnonzero(plain_to_vpn.train_mask))


SEEN: list[set[int]] = []


class SpyClassifier(ClassifierMixin, BaseEstimator):
    """Zapamiętuje, na których wierszach był dopasowany (także w strojeniu)."""

    def __init__(self, depth: int = 1):
        self.depth = depth

    def fit(self, X, y):
        SEEN.append(set(X.index))
        self.classes_ = np.unique(y)
        self.majority_ = pd.Series(y).mode().iloc[0]
        return self

    def predict(self, X):
        return np.full(len(X), self.majority_)


@dataclass(frozen=True)
class SpySpec(ModelSpec):
    def pipeline(self, seed: int = 42) -> Pipeline:
        return Pipeline([("clf", self.make(seed))])


@pytest.mark.parametrize("kind", ["session", "random"])
def test_tuning_sees_only_the_training_part(kind):
    data = make_data()
    spy = SpySpec("spy", lambda seed: SpyClassifier(), {"depth": [1, 2]})
    outcomes = run_cv(data, spy, SplitSpec(kind), n_jobs=1)
    for _ in range(5):
        SEEN.clear()
        outcome = next(outcomes)
        # 2 kandydatów x 3 foldy wewnętrzne + refit
        assert len(SEEN) == 7
        assert set().union(*SEEN) <= set(outcome.train_idx)
        assert not set().union(*SEEN) & set(outcome.test_idx)


def test_fold_without_enough_sessions_fails_loudly():
    data = make_data(sessions_per_class=3)
    with pytest.raises(ValueError, match="za mało sesji"):
        list(run_cv(data, get_model("dummy"), SplitSpec("session"), n_jobs=1))


def test_run_cv_with_a_tuned_model():
    data = make_data()
    outcomes = list(run_cv(data, get_model("tree"), SplitSpec("session"), n_jobs=1))
    assert [(o.repeat, o.fold) for o in outcomes] == [(0, f) for f in range(5)]
    for o in outcomes:
        assert set(o.best_params) == {"max_depth", "min_samples_leaf", "criterion"}
        assert 0 <= o.inner_best_f1 <= 1
        metrics = fold_metrics(data.y.iloc[o.test_idx], o.y_pred,
                               data.groups.iloc[o.test_idx], CLASSES)
        assert metrics["f1_macro"] > 0.9


def test_fold_metrics_on_a_hand_computed_example():
    y_true = pd.Series(["VoIP", "VoIP", "VoIP", "Video"])
    y_pred = np.array(["VoIP", "VoIP", "Video", "Video"])
    groups = pd.Series([1, 1, 2, 3])
    m = fold_metrics(y_true, y_pred, groups, CLASSES)
    # VoIP: tp=2, fn=1 -> 0,8; Video: tp=1, fp=1 -> 2/3
    assert m["f1_VoIP"] == pytest.approx(0.8)
    assert m["f1_Video"] == pytest.approx(2 / 3)
    assert m["f1_macro"] == pytest.approx((0.8 + 2 / 3) / 2)
    assert m["accuracy"] == pytest.approx(0.75)
    # wagi 1/rozmiar sesji: sesja 1 liczy się jak jeden przepływ -> VoIP tp=1, fn=1
    assert m["f1_macro_session_weighted"] == pytest.approx(2 / 3)
    assert m["largest_test_session_share"] == pytest.approx(0.5)
    assert (m["n_test_flows_VoIP"], m["n_test_sessions_VoIP"]) == (3, 2)
    assert (m["n_test_flows_Video"], m["n_test_sessions_Video"]) == (1, 1)
    assert m["confusion"] == [[2, 1], [0, 1]]
