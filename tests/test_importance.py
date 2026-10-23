import numpy as np
import pandas as pd
import pytest

from features import feature_group
from importance import gini_by_group, group_permutation_importance
from models import get_model

LABELS = ("VoIP", "Video")
# a1 i a2 to prawie ta sama informatywna cecha; b to szum
GROUPS = {"A": ["a1", "a2"], "B": ["b"]}


@pytest.fixture(scope="module")
def data():
    rng = np.random.default_rng(0)
    y = pd.Series(np.where(rng.random(400) < 0.5, "VoIP", "Video"))
    signal = (y == "Video").to_numpy() * 2.0 + rng.normal(0, 0.3, len(y))
    X = pd.DataFrame({"a1": signal, "a2": signal + rng.normal(0, 0.05, len(y)),
                      "b": rng.normal(0, 1, len(y))})
    return X, y


def fitted(name, X, y):
    return get_model(name).pipeline().fit(X, y)


def test_only_the_informative_group_loses_f1_when_permuted(data):
    X, y = data
    imp = group_permutation_importance(fitted("rf", X, y), X, y, LABELS, GROUPS)
    imp = imp.set_index("group")
    assert imp.loc["A", "perm_mean"] > 0.4
    assert abs(imp.loc["B", "perm_mean"]) < 0.05
    assert imp.loc["A", "n_features"] == 2
    assert (imp["f1_base"] > 0.95).all()


def test_permutation_is_deterministic_and_leaves_input_untouched(data):
    X, y = data
    before = X.copy()
    model = fitted("rf", X, y)
    first = group_permutation_importance(model, X, y, LABELS, GROUPS, seed=1)
    second = group_permutation_importance(model, X, y, LABELS, GROUPS, seed=1)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(X, before)


def test_gini_by_group_sums_feature_importances(data):
    X, y = data
    gini = gini_by_group(fitted("tree", X, y), GROUPS)
    assert sum(gini.values()) == pytest.approx(1.0)
    assert gini["A"] > gini["B"]


def test_gini_needs_a_tree_based_model(data):
    X, y = data
    with pytest.raises(TypeError, match="feature_importances_"):
        gini_by_group(fitted("knn", X, y), GROUPS)


@pytest.mark.parametrize("name, group", [
    ("Idle Mean", "przeciek_czasu"), ("Idle Min", "przeciek_czasu"),
    ("Flow Duration", "czasowe"), ("Fwd IAT Total", "czasowe"),
    ("Flow Bytes/s", "tempo"), ("Bwd Bulk Rate Avg", "tempo"),
    ("Packet Length Mean", "rozmiarowe"), ("Fwd Seg Size Min", "tcp_protokol"),
    ("Protocol", "tcp_protokol"), ("Down/Up Ratio", "licznosci"),
])
def test_feature_group_assignment(name, group):
    assert feature_group(name) == group
