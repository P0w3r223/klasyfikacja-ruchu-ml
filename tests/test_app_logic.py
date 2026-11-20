"""Logika aplikacji (etap 09) na małych danych sztucznych, bez plików .joblib."""
import io

import numpy as np
import pandas as pd
import pytest
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

import app_logic

FEATURES = ["Protocol", "Flow Duration", "Fwd Packet Length Max"]
META = {"features": FEATURES, "input_columns": [*FEATURES, "Src Port", "Dst Port", "Dst IP"],
        "label_column": "Label.1"}


def flows(n: int = 6, **overrides) -> pd.DataFrame:
    base = {"Src IP": "10.0.0.1", "Src Port": 50000, "Dst IP": "10.0.0.2", "Dst Port": 443,
            "Protocol": 6, "Flow Duration": 1000.0, "Fwd Packet Length Max": 100.0,
            "Label": "NonVPN", "Label.1": "Browsing"}
    df = pd.DataFrame([base] * n)
    return df.assign(**overrides)


def test_missing_columns_named_in_error():
    with pytest.raises(app_logic.InputError, match="Fwd Packet Length Max, Dst IP"):
        app_logic.prepare_input(flows().drop(columns=["Dst IP", "Fwd Packet Length Max"]), META)


def test_background_and_invalid_rows_removed_and_counted():
    df = flows(6)
    df.loc[0, "Dst Port"] = 53                 # DNS
    df.loc[1, "Dst IP"] = "224.0.0.251"        # multicast
    df.loc[2, "Protocol"] = 1                  # ICMP
    df.loc[3, "Flow Duration"] = np.inf
    prepared = app_logic.prepare_input(df, META)
    assert list(prepared.flows.index) == [4, 5]
    assert prepared.n_read == 6 and prepared.removed_invalid == 1
    assert prepared.removed_background.to_dict() == {
        "DNS": 1, "multicast/broadcast": 1, "protokół inny niż TCP/UDP": 1}
    assert list(prepared.X.columns) == FEATURES


def test_duplicates_are_kept():
    prepared = app_logic.prepare_input(flows(3), META)
    assert len(prepared.flows) == 3


def test_labels_mapped_like_preprocess():
    df = flows(4).assign(**{"Label.1": ["Browsing", "VOIP", "Video-Streaming ", "Chat"]})
    y = app_logic.prepare_input(df, META).y
    assert y.iloc[:3].tolist() == ["WWW", "VoIP", "Video"] and pd.isna(y.iloc[3])


def test_no_label_column_gives_no_labels():
    assert app_logic.prepare_input(flows().drop(columns=["Label.1"]), META).y is None


def test_only_background_is_an_input_error():
    with pytest.raises(app_logic.InputError, match="nie został"):
        app_logic.prepare_input(flows().assign(**{"Dst Port": 53}), META)


def test_empty_file_is_an_input_error():
    with pytest.raises(app_logic.InputError, match="żadnego"):
        app_logic.prepare_input(flows().iloc[:0], META)


def test_read_csv_names_second_label_column():
    data = b"Dst IP,Label,Label\n10.0.0.2,NonVPN,VOIP\n"
    assert list(app_logic.read_flows_csv(io.BytesIO(data)).columns) == ["Dst IP", "Label",
                                                                        "Label.1"]


def test_read_csv_errors_become_input_errors():
    with pytest.raises(app_logic.InputError):
        app_logic.read_flows_csv(io.BytesIO(b""))


@pytest.fixture
def separable():
    rng = np.random.default_rng(0)
    n = 80
    y = pd.Series(np.where(np.arange(n) < n // 2, "WWW", "Video"))
    X = pd.DataFrame({"Protocol": 6.0, "Flow Duration": rng.normal(0, 1, n),
                      "Fwd Packet Length Max": np.where(y == "WWW", 0.0, 10.0)
                      + rng.normal(0, 0.1, n)})
    return X, y


def test_predict_returns_class_and_confidence(separable):
    X, y = separable
    model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=3)).fit(X, y)
    out = app_logic.predict(model, X)
    assert (out["klasa"] == y).all()
    assert out["pewność"].between(0.5, 1.0).all() and out.index.equals(X.index)


def test_class_distribution_keeps_all_classes():
    dist = app_logic.class_distribution(pd.Series(["WWW", "WWW"]), ["WWW", "VoIP", "Video"])
    assert dist.to_dict() == {"WWW": 2, "VoIP": 0, "Video": 0}


def test_evaluate_counts_labels_outside_task():
    y_true = pd.Series(["WWW", "Video", "Video", "VoIP", None])
    y_pred = pd.Series(["WWW", "Video", "WWW", "Video", "WWW"])
    ev = app_logic.evaluate(y_true, y_pred, ["WWW", "Video"])
    assert ev.n_evaluated == 3
    assert ev.confusion.to_numpy().tolist() == [[1, 0], [1, 1]]
    assert ev.f1_per_class.round(3).to_dict() == {"WWW": 0.667, "Video": 0.667}
    assert ev.outside_classes.to_dict() == {"VoIP": 1, "nieznana": 1}


def test_evaluate_single_class_file_averages_present_classes():
    ev = app_logic.evaluate(pd.Series(["Video"] * 3), pd.Series(["Video"] * 3), ["WWW", "Video"])
    assert ev.f1_macro == 1.0 and ev.absent_classes == ["WWW"]
    assert ev.f1_per_class["WWW"] == 0.0


def test_too_many_flows_is_an_input_error(monkeypatch):
    monkeypatch.setattr(app_logic, "MAX_INPUT_FLOWS", 5)
    with pytest.raises(app_logic.InputError, match="najwyżej 5"):
        app_logic.prepare_input(flows(6), META)


def test_missing_file_is_an_input_error(tmp_path):
    with pytest.raises(app_logic.InputError):
        app_logic.read_flows_csv(str(tmp_path / "brak.csv"))


def test_evaluate_none_without_task_labels():
    assert app_logic.evaluate(pd.Series(["VoIP"]), pd.Series(["WWW"]), ["WWW", "Video"]) is None


def test_builtin_importance_only_for_tree_models(separable):
    X, y = separable
    tree = make_pipeline(StandardScaler(), DecisionTreeClassifier(random_state=0)).fit(X, y)
    knn = make_pipeline(StandardScaler(), KNeighborsClassifier()).fit(X, y)
    imp = app_logic.builtin_importance(tree)
    assert imp.index[0] == "Fwd Packet Length Max" and imp.sum() == pytest.approx(1.0)
    assert app_logic.builtin_importance(knn) is None


def test_permutation_importance_ranks_informative_feature(separable, monkeypatch):
    X, y = separable
    model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=3)).fit(X, y)
    monkeypatch.setattr(app_logic, "PERMUTATION_MAX_FLOWS", 40)  # próbka mniejsza niż plik
    ranking = app_logic.file_permutation_importance(model, X, y, ["WWW", "Video"])
    assert ranking.index[0] == "Fwd Packet Length Max" and ranking.iloc[0] > 0.3
    assert ranking["Protocol"] == 0.0


def test_permutation_importance_needs_task_labels(separable):
    X, y = separable
    model = make_pipeline(StandardScaler(), KNeighborsClassifier()).fit(X, y)
    with pytest.raises(app_logic.InputError):
        app_logic.file_permutation_importance(model, X, pd.Series("VoIP", index=X.index),
                                              ["WWW", "Video"])
