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
from train import main, prepare, resolve_features

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
    return path


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
    data = prepare(flows, TASKS["voip_video_vpncamp"], resolve_features("all"), 5.0)
    assert set(data.y) == {"VoIP", "Video"}
    assert data.train_mask.all() and data.test_mask.all()
    assert set(data.strata) == {"VoIP|plain", "VoIP|vpn", "Video|plain", "Video|vpn"}


def test_e3_plain_to_vpn_trains_on_all_plain_and_reuses_vpn_folds(flows_path):
    flows, features = load_flows(path=flows_path), resolve_features("all")
    cross = prepare(flows, TASKS["voip_video_plain2vpn"], features, 5.0)
    vpn = prepare(flows, TASKS["voip_video_vpn"], features, 5.0)
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
    at_5 = prepare(flows, task, features, 5.0).groups.nunique()
    at_15 = prepare(flows, task, features, 15.0).groups.nunique()
    assert (at_5, at_15) == (4 * SESSIONS_PER_GROUP, 4 * SESSIONS_PER_GROUP // 2)


def test_prepare_groups_by_ip_pair_regardless_of_time(flows_path):
    flows = load_flows(path=flows_path)
    data = prepare(flows, TASKS["voip_video_vpncamp"], resolve_features("all"), 5.0,
                   group_by="ip_pair")
    # 4 klasy×tunele, w każdej pary IP 10.0.g.0 … 10.0.g.4 z tym samym serwerem
    assert data.groups.nunique() == 4 * SESSIONS_PER_GROUP // 2


def test_ip_pair_ignores_direction():
    df = pd.DataFrame({"Src IP": ["10.0.0.1", "9.9.9.9"], "Dst IP": ["9.9.9.9", "10.0.0.1"]})
    assert ip_pair(df).nunique() == 1


def test_unknown_grouping_fails_with_a_list_of_options(flows_path):
    with pytest.raises(KeyError, match="dostępne"):
        prepare(load_flows(path=flows_path), TASKS["voip_video_vpncamp"],
                resolve_features("all"), 5.0, group_by="brak")


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
    exp = Experiment("test_imp", "voip_video_vpncamp", ("dummy", "tree"), ("session",),
                     importance_models=("tree",))
    monkeypatch.setitem(experiments.EXPERIMENTS, exp.name, exp)
    imp = pd.read_csv(run_cli(flows_path, tmp_path, exp) / "importance.csv")

    n_groups = len(feature_groups())
    assert len(imp) == 5 * n_groups
    assert set(imp["model"]) == {"tree"}
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


def test_prepare_takes_the_built_gap_from_features_json(flows_path, monkeypatch):
    monkeypatch.setattr(train, "built_session_gap_min", lambda: 15.0)
    data = prepare(load_flows(path=flows_path), TASKS["voip_video_vpncamp"],
                   resolve_features("all"), 15.0)
    assert data.groups.nunique() == 4 * SESSIONS_PER_GROUP
