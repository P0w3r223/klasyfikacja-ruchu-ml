"""E7, krok 2: metryki, wynik CV z E4, rozbicie czułości, przesunięcie cech, pliki do pokazu."""
import json

import numpy as np
import pandas as pd
import pytest

import e7
import e7_ocena as ev
from darknet_csv import ID_COLS, TIMESTAMP_FORMAT, sample_per_service, to_darknet_frame
from model_store import missing_input_columns
from preprocess import background_reason
from usbvpn import vpn_file_summary

FEATS = ["Protocol", "Flow Duration", "Total Fwd Packet", "Total Bwd packets"]
META = {"features": FEATS, "input_columns": ["Protocol", "Src Port", "Dst Port", "Dst IP",
                                             *FEATS[1:]],
        "label_column": "Label.1"}


def flows(services: list[str], seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(services)
    return pd.DataFrame({
        "service": services, "ts": pd.date_range("2022-10-17 13:05", periods=n, freq="s"),
        "Src Port": rng.integers(40000, 60000, n), "Dst Port": 443,
        "Protocol": rng.choice([6.0, 17.0], n), "Flow Duration": rng.random(n) * 1e6 / 3,
        "Total Fwd Packet": rng.integers(1, 40, n).astype(float),
        "Total Bwd packets": rng.integers(0, 40, n).astype(float)})


def test_metrics_per_class_and_confusion():
    y_true = np.array(["WWW"] * 4 + ["Video"] * 2)
    y_pred = np.array(["WWW", "WWW", "WWW", "Video", "Video", "WWW"])
    m = ev.metrics(y_true, y_pred, ["WWW", "Video"])
    assert m["confusion"] == [[3, 1], [1, 1]]
    assert m["recall_WWW"] == pytest.approx(0.75) and m["recall_Video"] == pytest.approx(0.5)
    assert m["balanced_accuracy"] == pytest.approx(0.625)
    assert m["f1_macro"] == pytest.approx((0.75 + 0.5) / 2)
    assert m["n_WWW"] == 4 and m["n_Video"] == 2


def test_majority_baseline_matches_constant_prediction():
    y = np.array(["WWW"] * 9 + ["Video"])
    # F1 WWW = 2·0,9/(1+0,9), F1 Video = 0
    assert ev.majority_baseline(y, ["WWW", "Video"]) == pytest.approx(0.9 / 1.9)


def test_task_population_requires_every_class():
    usb = flows(["WWW", "Video", "WWW"])
    assert len(ev.task_population(usb, ["WWW", "Video"])) == 3
    with pytest.raises(ValueError, match="VoIP"):
        ev.task_population(usb, ["VoIP", "Video"])


def test_cv_reference_reads_summary_and_confusion_in_json_class_order(tmp_path):
    pd.DataFrame({"model": ["rf", "rf"], "split": ["random", "session"],
                  "f1_macro_mean": [0.99, 0.80], "f1_macro_std": [0.0, 0.01]}
                 ).to_csv(tmp_path / "summary.csv", index=False)
    # kolejność klas w confusion.json inna niż w zadaniu
    conf = {"rf/session": {"classes": ["Video", "WWW"], "total": [[3, 1], [2, 8]]}}
    (tmp_path / "confusion.json").write_text(json.dumps(conf), encoding="utf-8")
    cv = ev.cv_reference(tmp_path, "rf", ["WWW", "Video"])
    assert cv["f1_macro"] == 0.80 and cv["f1_macro_std"] == 0.01
    assert cv["recall_WWW"] == pytest.approx(0.8) and cv["recall_Video"] == pytest.approx(0.75)
    with pytest.raises(ValueError, match="knn/session"):
        ev.cv_reference(tmp_path, "knn", ["WWW", "Video"])


def test_flow_buckets_length_port_and_protocol():
    df = pd.DataFrame({"Total Fwd Packet": [1, 3, 10, 30], "Total Bwd packets": [1, 0, 10, 0],
                       "Src Port": [50000, 80, 50001, 50002], "Dst Port": [443, 50003, 1433, 443],
                       "Protocol": [6.0, 6.0, 17.0, 17.0]})
    b = ev.flow_buckets(df)
    assert b["długość"].tolist() == ["≤ 3 pakiety", "≤ 3 pakiety", "4–20 pakietów",
                                     "≥ 21 pakietów"]  # 20 pakietów to jeszcze przedział środkowy
    assert b["port"].tolist() == ["443", "80", "inny", "443"]
    assert b["protokół"].tolist() == ["TCP", "TCP", "UDP", "UDP"]


def test_recall_breakdown_counts_hits_per_bucket():
    df = flows(["WWW", "WWW", "Video", "Video"]).assign(Protocol=[6.0, 17.0, 6.0, 17.0])
    pred = np.array(["WWW", "Video", "Video", "Video"])
    b = ev.recall_breakdown(df, pred, ["WWW", "Video"])
    proto = b[b["by"] == "protokół"].set_index(["service", "value"])
    assert proto.loc[("WWW", "TCP"), "recall"] == 1.0
    assert proto.loc[("WWW", "UDP"), "recall"] == 0.0
    assert proto.loc[("Video", "UDP"), "n"] == 1
    assert set(b["by"]) == {"protokół", "długość", "port"}


def test_feature_shift_weights_ks_by_importance_and_averages_video_campaigns():
    ks = pd.DataFrame({"reference": ["WWW (Tor-nonTor)", "Video (Tor-nonTor)",
                                     "Video (VPN-nonVPN)", "VoIP (VPN-nonVPN)"] * 2,
                       "feature": ["a"] * 4 + ["b"] * 4,
                       "ks": [0.2, 0.4, 0.8, 0.1, 0.0, 0.0, 0.0, 0.0]})
    imp = pd.Series({"a": 0.75, "b": 0.25})
    s = ev.feature_shift(imp, ks, "uslugi3_plain")
    assert s.loc["a", "ks_Video"] == pytest.approx(0.6)  # średnia z obu kampanii
    assert s.loc["a", "ks_mean"] == pytest.approx((0.2 + 0.1 + 0.6) / 3)
    assert s.loc["a", "shift_weighted"] == pytest.approx(0.75 * 0.3)
    assert s.index[0] == "a"
    with pytest.raises(ValueError, match="c"):
        ev.feature_shift(pd.Series({"c": 1.0}), ks, "www_video_tor")


def test_darknet_frame_reads_back_like_darknet_csv(tmp_path):
    src = flows(["WWW", "Video", "VoIP"])
    path = tmp_path / "demo.csv"
    to_darknet_frame(src, FEATS, "NonVPN").to_csv(path, index=False)
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header[:7] == ID_COLS and header[-2:] == ["Label", "Label"]
    back = pd.read_csv(path)
    assert missing_input_columns(list(back.columns), META, require_label=True) == []
    assert back["Label"].eq("NonVPN").all()
    assert back["Label.1"].tolist() == ["Browsing", "Video-Streaming", "VOIP"]
    assert (background_reason(back) == "").all()
    ts = pd.to_datetime(back["Timestamp"], format=TIMESTAMP_FORMAT)
    assert (ts == src["ts"].dt.floor("s").to_numpy()).all()
    with pytest.raises(ValueError, match="Audio"):
        to_darknet_frame(flows(["Audio"]), FEATS, "NonVPN")


def test_missing_input_columns_names_absent_columns():
    cols = ["Protocol", "Src Port", "Dst IP", *FEATS[1:]]
    assert missing_input_columns(cols, META) == ["Dst Port"]
    assert missing_input_columns(cols, META, require_label=True) == ["Dst Port", "Label.1"]


def test_sample_per_service_caps_at_available_and_is_reproducible():
    src = flows(["WWW"] * 50 + ["VoIP"] * 3)
    a = sample_per_service(src, {"WWW": 10, "VoIP": 62}, seed=42)
    b = sample_per_service(src, {"WWW": 10, "VoIP": 62}, seed=42)
    assert a["service"].value_counts().to_dict() == {"WWW": 10, "VoIP": 3}
    assert a.index.equals(b.index) and a["ts"].is_monotonic_increasing
    with pytest.raises(ValueError, match="Video"):
        sample_per_service(src, {"Video": 1}, seed=42)


def test_check_demo_file_rejects_changed_features(tmp_path):
    src = flows(["WWW", "Video"])
    path = tmp_path / "demo.csv"
    to_darknet_frame(src, FEATS, "NonVPN").to_csv(path, index=False)
    e7.check_demo_file(path, src, META)
    with pytest.raises(ValueError, match="cechy"):
        e7.check_demo_file(path, src.assign(**{"Flow Duration": src["Flow Duration"] + 1}), META)
    with pytest.raises(ValueError, match="kolumn"):
        e7.check_demo_file(path, src, {**META, "input_columns": [*META["input_columns"], "X"]})


def test_vpn_file_summary_counts_connections_and_top_share():
    recs = [{"ip_proto": "udp", "port_src": 1701, "port_dst": 1701, "x_packets": [{}] * 90},
            {"ip_proto": "udp", "port_src": 1701, "port_dst": 1701, "x_packets": [{}] * 60},
            {"ip_proto": "tcp", "port_src": 50000, "port_dst": 443, "x_packets": [{}] * 50}]
    s = vpn_file_summary(recs)
    assert s["records"] == 3 and s["entries"] == 200 and s["connections"] == 2
    assert s["connections_100"] == 1 and s["top_connection"] == "udp/1701/1701"
    assert s["top1_share"] == pytest.approx(0.75) and s["top2_share"] == pytest.approx(1.0)
    assert vpn_file_summary([])["top_connection"] == ""
