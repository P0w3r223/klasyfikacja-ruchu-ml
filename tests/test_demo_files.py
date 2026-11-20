"""Wycinanie plików do pokazu (etap 09) ze sztucznego surowego pliku jak z load_raw."""
import pandas as pd
import pytest

import demo_files

HOST, PEER, OTHER, RESOLVER = "10.0.0.5", "93.184.216.34", "151.101.1.1", "10.0.0.1"
SESSION = {"traffic_type": "NonVPN", "service": "VoIP", "campaign": "vpn-nonvpn",
           "tunnel": "plain", "ip_a": HOST, "ip_b": PEER,
           "ts_min": "2015-04-29 10:50:00", "ts_max": "2015-04-29 10:52:00", "n_flows": 3}


def row(src, dst, dport, minute, duration, service="VoIP", traffic="NonVPN"):
    ts = pd.Timestamp("2015-04-29 10:00:00") + pd.Timedelta(minutes=minute)
    return {"Flow ID": f"{src}-{dst}-{dport}", "Src IP": src, "Src Port": 50000,
            "Dst IP": dst, "Dst Port": dport, "Protocol": 17,
            "Timestamp": ts.strftime(demo_files.RAW_TS_FORMAT), "Flow Duration": duration,
            "Total Fwd Packet": 3.0, "traffic_type": traffic, "service_raw": service.upper(),
            "service": service}


@pytest.fixture
def raw():
    rows = [
        row(HOST, PEER, 5060, 20, 777.0),        # 0: wcześniejsza kopia wiersza 3 (trening)
        row(HOST, PEER, 5060, 50, 100.0),        # 1-2: sesja
        row(PEER, HOST, 5060, 51, 200.0),
        row(HOST, PEER, 5060, 51, 777.0),        # 3: duplikat wiersza 0, nie ma go w flows
        row(HOST, PEER, 5060, 52, 300.0),        # 4: sesja
        row(HOST, RESOLVER, 53, 50, 1.0),        # 5-7: tło hosta w oknie
        row(HOST, RESOLVER, 53, 51, 2.0),
        row(HOST, "224.0.0.252", 5355, 51, 3.0),
        row(HOST, RESOLVER, 53, 55, 4.0),        # 8: tło poza oknem
        row(HOST, OTHER, 443, 51, 5.0),          # 9: inna para w oknie (inna sesja)
        row(HOST, PEER, 5060, 51, 6.0, traffic="VPN"),  # 10: inna etykieta
    ]
    return pd.DataFrame(rows)


def test_selects_session_and_capped_background(raw):
    out = demo_files.select_demo_rows(raw, [SESSION], max_background=2)
    session = {1, 2, 4}
    assert session <= set(out.index)
    background = set(out.index) - session
    assert len(background) == 2 and background <= {5, 6, 7}
    assert not {8, 9, 10} & set(out.index)  # tło poza oknem, inna para, inna etykieta
    assert demo_files.raw_timestamps(out).is_monotonic_increasing


def test_duplicate_of_training_flow_is_left_out(raw):
    out = demo_files.select_demo_rows(raw, [SESSION], max_background=0)
    assert set(out.index) == {1, 2, 4}


def test_count_mismatch_stops(raw):
    with pytest.raises(ValueError, match="zamiast 4"):
        demo_files.select_demo_rows(raw, [{**SESSION, "n_flows": 4}], max_background=0)


def test_raw_column_names_restored(raw, tmp_path):
    out = demo_files.to_raw_columns(raw.loc[[1, 5]])
    assert list(out.columns[-2:]) == ["Label", "Label"] and "service" not in out.columns
    path = tmp_path / "demo.csv"
    out.to_csv(path, index=False)
    back = pd.read_csv(path)
    assert back["Label"].tolist() == ["NonVPN", "NonVPN"]
    assert back["Label.1"].tolist() == ["VOIP", "VOIP"]
