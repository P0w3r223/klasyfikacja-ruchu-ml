"""Test integracyjny src/train.py: eksperyment na syntetycznym flows.parquet."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from evaluate import SplitSpec, outer_folds
import experiments
from experiments import TASKS, Experiment
from features import PROCESSED, feature_groups, feature_list, load_flows
from preprocess import META_COLS, assign_sessions, ip_pair
import train
from train import git_provenance, main, prepare, resolve_features

TRAFFIC_TYPE = {("vpn-nonvpn", "plain"): "NonVPN", ("vpn-nonvpn", "vpn"): "VPN",
                ("tor-nontor", "plain"): "Non-Tor"}
SESSIONS_PER_GROUP = 10
TIME_COLS = ["fit_s", "search_s", "predict_s"]


def synthetic_flows(rng: np.random.Generator) -> pd.DataFrame:
    """Sesje 2j i 2j+1 mają tę samą parę IP i ok. 9 min przerwy: przy progu 15 min się łączą."""
    features = feature_list()
    groups = [("vpn-nonvpn", "plain", "VoIP"), ("vpn-nonvpn", "plain", "Video"),
              ("vpn-nonvpn", "vpn", "VoIP"), ("vpn-nonvpn", "vpn", "Video"),
              ("tor-nontor", "plain", "WWW")]
    rows, session = [], 0
    base = pd.Timestamp("2015-02-23 10:00:00")
    for g, (campaign, tunnel, service) in enumerate(groups):
        for k in range(SESSIONS_PER_GROUP):
            for i in range(4 + k % 3):
                rows.append({
                    "traffic_type": TRAFFIC_TYPE[(campaign, tunnel)], "service": service,
                    "campaign": campaign, "tunnel": tunnel, "session": session,
                    "ts": base + pd.Timedelta(minutes=10 * k, seconds=10 * i),
                    "Src IP": f"10.0.{g}.{k // 2}", "Dst IP": "9.9.9.9",
                    "Src Port": 40000 + i, "Dst Port": 443,
                    **dict(zip(features, rng.normal(3.0 * (service == "Video"), 1.0,
                                                    len(features)))),
                })
            session += 1
    return pd.DataFrame(rows)[META_COLS + features]


@pytest.fixture(scope="module")
def flows_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "flows.parquet"
    synthetic_flows(np.random.default_rng(0)).to_parquet(path, index=False)
    write_features_json(path, gap_min=5.0)
    return path


def write_features_json(flows_path, gap_min):
    """preprocess.py zapisuje features.json obok flows.parquet; train.py czyta z niego próg."""
    flows_path.with_name("features.json").write_text(
        json.dumps({"features": feature_list(), "session_gap_min": gap_min}), encoding="utf-8")


@pytest.fixture
def small_experiment(monkeypatch):
    exp = Experiment("test_cli", "voip_video_vpncamp", ("dummy", "tree"), ("random", "session"))
    monkeypatch.setitem(experiments.EXPERIMENTS, exp.name, exp)
    return exp


def run_cli(flows_path, out, exp):
    main(["--experiment", exp.name, "--data", str(flows_path), "--out", str(out),
          "--n-jobs", "1"])
    return out / exp.name


def test_cli_writes_all_results(flows_path, tmp_path, small_experiment):
    out_dir = run_cli(flows_path, tmp_path, small_experiment)

    folds = pd.read_csv(out_dir / "folds.csv")
    assert len(folds) == 2 * 2 * 5
    assert {"f1_macro", "f1_VoIP", "f1_Video", "n_test_sessions_VoIP",
            "largest_test_session_share", "best_params", *TIME_COLS} <= set(folds.columns)
    mean_f1 = folds.groupby("model")["f1_macro"].mean()
    assert mean_f1["tree"] > mean_f1["dummy"] + 0.3

    summary = pd.read_csv(out_dir / "summary.csv")
    assert len(summary) == 4
    assert (summary["n_folds"] == 5).all()
    assert summary["f1_macro_oof"].between(0, 1).all()

    confusion = json.loads((out_dir / "confusion.json").read_text(encoding="utf-8"))
    total = np.array(confusion["tree/session"]["total"])
    n_task = 2 * 2 * sum(4 + k % 3 for k in range(SESSIONS_PER_GROUP))
    assert total.sum() == n_task

    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    assert run["data"]["sha256"] == hashlib.sha256(flows_path.read_bytes()).hexdigest()
    assert run["experiment"]["name"] == "test_cli"
    assert (out_dir / "predictions.parquet").exists()


def test_cli_is_deterministic(flows_path, tmp_path, small_experiment):
    first = pd.read_csv(run_cli(flows_path, tmp_path / "a", small_experiment) / "folds.csv")
    second = pd.read_csv(run_cli(flows_path, tmp_path / "b", small_experiment) / "folds.csv")
    pd.testing.assert_frame_equal(first.drop(columns=TIME_COLS),
                                  second.drop(columns=TIME_COLS))


def test_prepare_selects_task_population(flows_path):
    flows = load_flows(path=flows_path)
    data = prepare(flows, TASKS["voip_video_vpncamp"], resolve_features("all"), 5.0,
                   built_gap_min=5.0)
    assert set(data.y) == {"VoIP", "Video"}
    assert data.train_mask.all() and data.test_mask.all()
    assert set(data.strata) == {"VoIP|plain", "VoIP|vpn", "Video|plain", "Video|vpn"}


def test_e3_plain_to_vpn_trains_on_all_plain_and_reuses_vpn_folds(flows_path):
    flows, features = load_flows(path=flows_path), resolve_features("all")
    cross = prepare(flows, TASKS["voip_video_plain2vpn"], features, 5.0, built_gap_min=5.0)
    vpn = prepare(flows, TASKS["voip_video_vpn"], features, 5.0, built_gap_min=5.0)
    spec = SplitSpec("session", n_outer=3)
    plain_rows = np.flatnonzero(cross.train_mask)
    assert set(cross.X.index[cross.test_mask]).isdisjoint(plain_rows)
    for (train_idx, test_idx), (_, vpn_test) in zip(outer_folds(cross, spec, 0),
                                                    outer_folds(vpn, spec, 0)):
        np.testing.assert_array_equal(train_idx, plain_rows)
        pd.testing.assert_series_equal(cross.groups.iloc[test_idx].reset_index(drop=True),
                                       vpn.groups.iloc[vpn_test].reset_index(drop=True))


def test_prepare_recomputes_sessions_for_another_gap(flows_path):
    flows = load_flows(path=flows_path)
    task, features = TASKS["voip_video_vpncamp"], resolve_features("all")
    at_5 = prepare(flows, task, features, 5.0, built_gap_min=5.0).groups.nunique()
    at_15 = prepare(flows, task, features, 15.0, built_gap_min=5.0).groups.nunique()
    assert (at_5, at_15) == (4 * SESSIONS_PER_GROUP, 4 * SESSIONS_PER_GROUP // 2)


def test_prepare_groups_by_ip_pair_regardless_of_time(flows_path):
    flows = load_flows(path=flows_path)
    data = prepare(flows, TASKS["voip_video_vpncamp"], resolve_features("all"), 5.0,
                   group_by="ip_pair", built_gap_min=5.0)
    # 4 klasy×tunele, w każdej pary IP 10.0.g.0 … 10.0.g.4 z tym samym serwerem
    assert data.groups.nunique() == 4 * SESSIONS_PER_GROUP // 2


def test_ip_pair_ignores_direction():
    df = pd.DataFrame({"Src IP": ["10.0.0.1", "9.9.9.9"], "Dst IP": ["9.9.9.9", "10.0.0.1"]})
    assert ip_pair(df).nunique() == 1


def test_unknown_grouping_fails_with_a_list_of_options(flows_path):
    with pytest.raises(KeyError, match="dostępne"):
        prepare(load_flows(path=flows_path), TASKS["voip_video_vpncamp"],
                resolve_features("all"), 5.0, group_by="brak", built_gap_min=5.0)


def same_partition(a: pd.Series, b: pd.Series) -> bool:
    pairs = pd.DataFrame({"a": a.to_numpy(), "b": b.to_numpy()})
    return (pairs.groupby("a")["b"].nunique().max() == 1
            and pairs.groupby("b")["a"].nunique().max() == 1)


def test_assign_sessions_at_5_min_reproduces_the_session_column(flows_path):
    flows = load_flows(path=flows_path)
    assert same_partition(flows["session"], assign_sessions(flows, 5.0))


@pytest.mark.skipif(not (PROCESSED / "flows.parquet").exists(), reason="brak flows.parquet")
def test_assign_sessions_reproduces_the_real_session_column():
    flows = load_flows(include_audio=True)
    assert same_partition(flows["session"], assign_sessions(flows, 5.0))


def test_feature_sets_drop_idle_and_tcp_shortcuts():
    all_features = resolve_features("all")
    no_idle = resolve_features("bez_idle")
    no_shortcuts = resolve_features("bez_skrotow")
    assert not any(f.startswith("Idle") for f in no_idle + no_shortcuts)
    assert len(no_idle) == len(all_features) - 4
    assert set(all_features) - set(no_shortcuts) == (
        set(all_features) - set(no_idle)) | set(experiments.TCP_SHORTCUTS)


def test_e4_feature_sets_follow_feature_groups():
    groups = feature_groups()
    no_idle = resolve_features("bez_idle")
    assert resolve_features("tylko_czasowe") == groups["czasowe"]
    assert set(resolve_features("czasowe_tempo")) == set(groups["czasowe"] + groups["tempo"])
    assert resolve_features("tylko_rozmiarowe") == groups["rozmiarowe"]
    assert resolve_features("bez_protocol") == [f for f in no_idle if f != "Protocol"]
    for name in experiments.E4_FEATURE_SETS:
        if name != "all":
            assert not set(resolve_features(name)) & set(groups["przeciek_czasu"])


def test_e4_covers_every_feature_set_and_03b_task_with_rf_importance():
    e4 = [e for e in experiments.EXPERIMENTS.values() if e.name.startswith("e4_")]
    assert {(e.feature_set, e.task) for e in e4} == {
        (fs, t) for fs in experiments.E4_FEATURE_SETS for t in experiments.TASKS_03B}
    assert all(e.importance_models == ("rf",) for e in e4)
    assert all(e.n_outer == experiments.OUTER_FOLDS.get(e.task, 5) for e in e4)


def test_cli_writes_group_importance_only_for_selected_models(flows_path, tmp_path,
                                                               monkeypatch):
    exp = Experiment("test_imp", "voip_video_vpncamp", ("dummy", "tree"), ("random", "session"),
                     importance_models=("tree",))
    monkeypatch.setitem(experiments.EXPERIMENTS, exp.name, exp)
    imp = pd.read_csv(run_cli(flows_path, tmp_path, exp) / "importance.csv")

    n_groups = len(feature_groups())
    assert len(imp) == 5 * n_groups
    assert set(imp["model"]) == {"tree"}
    assert set(imp["split"]) == {"session"}
    assert imp.groupby("fold")["gini"].sum().to_numpy() == pytest.approx(np.ones(5))
    assert {"group", "n_features", "f1_base", "perm_mean", "perm_std", "split",
            "repeat"} <= set(imp.columns)


def test_cli_skips_importance_file_when_not_requested(flows_path, tmp_path,
                                                      small_experiment):
    assert not (run_cli(flows_path, tmp_path, small_experiment) / "importance.csv").exists()


def test_unknown_names_fail_with_a_list_of_options():
    with pytest.raises(KeyError, match="dostępne"):
        resolve_features("brak")
    with pytest.raises(KeyError, match="dostępne"):
        main(["--experiment", "brak"])


def test_prepare_reuses_the_session_column_built_with_the_same_gap(flows_path):
    # kolumna session z progiem 5 min, ale opisana jako zbudowana przy 15 min: nie przeliczamy
    data = prepare(load_flows(path=flows_path), TASKS["voip_video_vpncamp"],
                   resolve_features("all"), 15.0, built_gap_min=15.0)
    assert data.groups.nunique() == 4 * SESSIONS_PER_GROUP


def test_cli_takes_the_built_gap_from_features_json_next_to_the_data(flows_path, tmp_path,
                                                                    monkeypatch):
    data = tmp_path / "data" / "flows.parquet"
    data.parent.mkdir()
    data.write_bytes(flows_path.read_bytes())
    write_features_json(data, gap_min=15.0)
    exp = Experiment("test_gap", "voip_video_vpncamp", ("dummy",), ("session",))
    monkeypatch.setitem(experiments.EXPERIMENTS, exp.name, exp)
    main(["--experiment", exp.name, "--data", str(data), "--out", str(tmp_path / "out"),
          "--n-jobs", "1"])
    run = json.loads((tmp_path / "out" / exp.name / "run.json").read_text(encoding="utf-8"))
    assert run["data"]["built_session_gap_min"] == 15.0
    assert "changed_during_run" in run


def test_cli_fails_without_features_json_next_to_the_data(flows_path, tmp_path,
                                                           small_experiment):
    data = tmp_path / "flows.parquet"
    data.write_bytes(flows_path.read_bytes())
    with pytest.raises(FileNotFoundError, match="features.json"):
        run_cli(data, tmp_path / "out", small_experiment)


@pytest.mark.parametrize("after, dirty, changed", [
    ({"commit": "a", "dirty": False}, False, False),
    ({"commit": "b", "dirty": False}, True, True),
    ({"commit": "a", "dirty": True}, True, True),
])
def test_git_state_changed_during_the_run_marks_results_dirty(after, dirty, changed):
    info = git_provenance({"commit": "a", "dirty": False}, after)
    assert (info["commit"], info["dirty"], info["changed_during_run"]) == ("a", dirty, changed)


def test_confusion_total_is_one_pass_of_cv_even_with_repeats():
    per_fold = [[[1, 0], [0, 1]], [[2, 0], [0, 2]], [[3, 0], [0, 3]], [[0, 0], [0, 0]]]
    assert train._confusion_total(per_fold[:2], [0, 0]) == [[3, 0], [0, 3]]
    assert train._confusion_total(per_fold, [0, 0, 1, 1]) == [[3.0, 0.0], [0.0, 3.0]]


def test_summarize_on_a_hand_computed_example():
    folds = pd.DataFrame({
        "model": "rf", "split": "session", "fold": [0, 1], "f1_macro": [0.5, 1.0],
        "f1_macro_session_weighted": [0.4, 0.8], "accuracy": [0.75, 1.0],
        "f1_VoIP": [0.0, 1.0], "f1_Video": [1.0, 1.0]})
    predictions = pd.DataFrame({
        "model": "rf", "split": "session", "repeat": 0,
        "y_true": ["VoIP", "Video", "VoIP", "Video"],
        "y_pred": ["Video", "Video", "VoIP", "Video"]})
    row = train.summarize(train.ExperimentResult(folds, predictions, {}),
                          ("VoIP", "Video")).iloc[0]
    assert row["f1_macro_mean"] == pytest.approx(0.75)
    assert row["f1_macro_min"] == 0.5 and row["f1_macro_max"] == 1.0
    assert row["n_folds"] == 2
    # OOF: VoIP tp=1, fn=1 -> 2/3; Video tp=2, fp=1 -> 0,8
    assert row["f1_macro_oof"] == pytest.approx((2 / 3 + 0.8) / 2)
