"""Test integracyjny src/train.py: eksperyment na syntetycznym flows.parquet."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

import experiments
from experiments import TASKS, Experiment
from features import PROCESSED, feature_list, load_flows
from preprocess import META_COLS, assign_sessions
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


def test_prepare_recomputes_sessions_for_another_gap(flows_path):
    flows = load_flows(path=flows_path)
    task, features = TASKS["voip_video_vpncamp"], resolve_features("all")
    at_5 = prepare(flows, task, features, 5.0).groups.nunique()
    at_15 = prepare(flows, task, features, 15.0).groups.nunique()
    assert (at_5, at_15) == (4 * SESSIONS_PER_GROUP, 4 * SESSIONS_PER_GROUP // 2)


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
