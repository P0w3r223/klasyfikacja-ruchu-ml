import pandas as pd
import pytest

from make_figures_04_e4 import (FEATURE_SET_ORDER, feature_set_table, importance_table,
                                model_ranking, n_features)


def test_feature_set_table_uses_only_the_session_split():
    folds = pd.DataFrame({
        "task": "t", "feature_set": "bez_idle", "model": "rf",
        "split": ["session", "session", "random"], "f1_macro": [0.8, 0.6, 0.99]})
    row = feature_set_table(folds).iloc[0]
    assert row["mean"] == pytest.approx(0.7)
    assert row["std"] == pytest.approx(0.1414, abs=1e-4)


def test_model_ranking_orders_trained_models_and_skips_dummy():
    table = pd.DataFrame({"task": "t", "feature_set": "all",
                          "model": ["dummy", "knn", "tree", "rf"],
                          "mean": [0.99, 0.7, 0.9, 0.8], "std": 0.0})
    assert model_ranking(table, "t", "all") == "drzewo > RF > k-NN"


def test_importance_table_averages_session_folds_per_group():
    imp = pd.DataFrame({
        "task": "t", "feature_set": "all", "group": "czasowe", "n_features": 15,
        "split": ["session", "session", "random"], "gini": [0.2, 0.4, 0.9],
        "perm_mean": [0.1, 0.3, 0.9]})
    row = importance_table(imp).iloc[0]
    assert (row["gini"], row["perm"]) == (pytest.approx(0.3), pytest.approx(0.2))
    assert row["n_features"] == 15


def test_feature_counts_match_the_registry():
    counts = n_features()
    assert list(counts) == FEATURE_SET_ORDER
    assert (counts["all"], counts["bez_idle"], counts["tylko_czasowe"],
            counts["czasowe_tempo"], counts["tylko_rozmiarowe"]) == (62, 58, 15, 20, 22)
