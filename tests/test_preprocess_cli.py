"""Test integracyjny src/preprocess.py: cały potok na syntetycznym CSV o układzie Darknet.CSV."""
import json

import pandas as pd
import pytest

from preprocess import META_COLS, build, load_raw, main

HEADER = ("Flow ID,Src IP,Src Port,Dst IP,Dst Port,Protocol,Timestamp,"
          "Flow Duration,Total Fwd Packet,Const Feat,Label,Label")
KEPT = [
    # WWW; drugi przepływ tej samej pary IP (odwrócony kierunek) 2 min później -> ta sama sesja
    "k1,10.0.0.1,50000,8.8.4.4,443,6,23/02/2015 10:00:00 AM,100,3,1,Non-Tor,Browsing",
    "k2,8.8.4.4,443,10.0.0.1,50001,6,23/02/2015 10:02:00 AM,200,4,1,Non-Tor,browsing",
    "k3,10.0.0.2,40000,9.9.9.9,5060,17,23/02/2015 10:00:00 AM,300,5,1,NonVPN,VOIP",
    "k4,10.8.0.2,40001,9.9.9.9,443,17,23/02/2015 10:00:00 AM,400,6,1,VPN,Video-Streaming",
    # Audio ma inną wartość Const Feat, ale o cechach stałych decyduje tylko ruch główny
    "k5,10.0.0.3,40002,9.9.9.8,443,6,23/02/2015 10:00:00 AM,500,7,9,NonVPN,Audio-Streaming",
]
DROPPED = [
    "d1,10.0.0.4,40003,9.9.9.7,443,6,23/02/2015 10:00:00 AM,600,8,1,Tor,Browsing",
    "d2,10.0.0.5,40004,9.9.9.6,443,6,23/02/2015 10:00:00 AM,700,9,1,NonVPN,Chat",
    "d3,10.0.0.6,40005,9.9.9.5,53,17,23/02/2015 10:00:00 AM,800,10,1,NonVPN,VoIP",
    "d4,10.0.0.7,40006,224.0.0.251,40007,17,23/02/2015 10:00:00 AM,900,11,1,Non-Tor,Browsing",
    "d5,10.0.0.8,0,9.9.9.4,0,0,23/02/2015 10:00:00 AM,1000,12,1,Non-Tor,Browsing",
    # duplikat k1: inne Flow ID i czas, te same cechy i etykiety
    "d6,10.0.0.1,50002,8.8.4.4,443,6,23/02/2015 11:00:00 AM,100,3,1,Non-Tor,Browsing",
    "d7,10.0.0.9,40007,9.9.9.3,443,6,23/02/2015 10:00:00 AM,,13,1,Non-Tor,Browsing",
]
# Za dużo pól, jak uszkodzony wiersz 328 - load_raw go pomija.
BAD_LINE = "bad,10.0.0.1,1,10.0.0.2,2,6,23/02/2015 10:00:00 AM,1,1,1,Non-Tor,Browsing,x,y,z"
FEATURES = ["Protocol", "Flow Duration", "Total Fwd Packet"]


@pytest.fixture(scope="module")
def raw_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("raw") / "Darknet.CSV"
    lines = [HEADER, *KEPT[:3], BAD_LINE, *KEPT[3:], *DROPPED]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_cli(raw_csv, root, *extra):
    out_dir, reports_dir = root / "out", root / "reports"
    main(["--raw", str(raw_csv), "--out-dir", str(out_dir),
          "--reports-dir", str(reports_dir), *extra])
    return out_dir, reports_dir


@pytest.fixture(scope="module")
def outputs(raw_csv, tmp_path_factory):
    return run_cli(raw_csv, tmp_path_factory.mktemp("run"))


def test_only_kept_flows_written(outputs):
    flows = pd.read_parquet(outputs[0] / "flows.parquet")
    assert sorted(flows["Flow Duration"]) == [100, 200, 300, 400, 500]
    assert flows["service"].value_counts().to_dict() == {
        "WWW": 2, "VoIP": 1, "Video": 1, "Audio": 1}


def test_flows_columns_and_dtypes(outputs):
    flows = pd.read_parquet(outputs[0] / "flows.parquet")
    assert flows.columns.tolist() == META_COLS + FEATURES
    assert (flows[FEATURES].dtypes == "float64").all()
    assert flows.set_index("Flow Duration")["tunnel"].to_dict() == {
        100: "plain", 200: "plain", 300: "plain", 400: "vpn", 500: "plain"}


def test_sessions_join_reversed_pair_within_gap(outputs):
    flows = pd.read_parquet(outputs[0] / "flows.parquet").set_index("Flow Duration")
    assert flows.loc[100, "session"] == flows.loc[200, "session"]
    assert flows["session"].nunique() == 4


def test_features_json_drops_constant_ignoring_audio(outputs):
    out_dir, reports_dir = outputs
    text = (out_dir / "features.json").read_text(encoding="utf-8")
    assert json.loads(text) == {
        "features": FEATURES, "dropped_constant": ["Const Feat"], "session_gap_min": 5.0}
    assert (reports_dir / "features.json").read_text(encoding="utf-8") == text


def test_report_counts_each_step(outputs):
    report = (outputs[1] / "preprocess_report.md").read_text(encoding="utf-8")
    for line in [
        "Surowy plik: 12 przepływów",
        "### 1. Podzbiór (bez Tor, 3 usługi + Audio do E5): 10 przepływów",
        "### 2. Po odfiltrowaniu ruchu tła: 7 przepływów",
        "Usunięte wiersze z inf/NaN: 1",
        "Usunięte duplikaty (te same cechy i etykiety): 1",
        "### 3. Po czyszczeniu: 5 przepływów",
        "Cechy stałe usunięte (1): Const Feat",
        "Cechy do modelowania: 3",
    ]:
        assert line in report


def test_report_lists_background_reasons(outputs):
    report = (outputs[1] / "preprocess_report.md").read_text(encoding="utf-8")
    background = report.split("### Odfiltrowany ruch tła")[1].split("###")[0]
    for reason in ["DNS", "multicast/broadcast", "protokół inny niż TCP/UDP"]:
        assert reason in background


def test_gap_min_flag_reaches_sessions_and_features_json(raw_csv, tmp_path):
    out_dir, _ = run_cli(raw_csv, tmp_path, "--gap-min", "1")
    flows = pd.read_parquet(out_dir / "flows.parquet").set_index("Flow Duration")
    assert flows.loc[100, "session"] != flows.loc[200, "session"]
    features = json.loads((out_dir / "features.json").read_text(encoding="utf-8"))
    assert features["session_gap_min"] == 1.0


def test_build_does_not_modify_input(raw_csv):
    raw = load_raw(raw_csv)
    before = raw.copy()
    build(raw, gap_min=5.0)
    pd.testing.assert_frame_equal(raw, before)
