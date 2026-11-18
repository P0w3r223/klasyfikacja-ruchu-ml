"""Cechy CICFlowMeter na przepływach policzonych ręcznie (etap 06, E7)."""
import math

import pytest

from cic_features import ACK, FIN, PSH, SYN, Packets, flow_features, split_flows


def Packet(ts, payload, sign, header, flags):  # noqa: N802 - krotka w kolejności Packets.of
    return (ts, payload, sign, header, flags)

T0 = 1_000_000


def tcp_flow() -> Packets:
    """Handshake, 100 B w przód, 1000 + 500 B wstecz, FIN w przód."""
    return Packets.of([
        Packet(T0, 0, +1, 32, SYN),
        Packet(T0 + 100, 0, -1, 32, SYN | ACK),
        Packet(T0 + 300, 0, +1, 20, ACK),
        Packet(T0 + 600, 100, +1, 20, PSH | ACK),
        Packet(T0 + 1000, 1000, -1, 20, ACK),
        Packet(T0 + 1500, 500, -1, 20, PSH | ACK),
        Packet(T0 + 2100, 0, +1, 20, FIN | ACK),
    ])


def test_tcp_flow_by_hand():
    f = flow_features(tcp_flow(), +1, 6)
    expected = {
        "Protocol": 6, "Flow Duration": 2100,
        "Total Fwd Packet": 4, "Total Bwd packets": 3,
        "Total Length of Fwd Packet": 100, "Total Length of Bwd Packet": 1500,
        "Fwd Packet Length Max": 100, "Fwd Packet Length Min": 0,
        "Fwd Packet Length Mean": 25, "Fwd Packet Length Std": 50,
        "Bwd Packet Length Max": 1000, "Bwd Packet Length Min": 0,
        "Bwd Packet Length Mean": 500, "Bwd Packet Length Std": 500,
        "Flow Bytes/s": 1600 / 0.0021, "Flow Packets/s": 7 / 0.0021,
        "Flow IAT Mean": 350, "Flow IAT Std": math.sqrt(35000),
        "Flow IAT Max": 600, "Flow IAT Min": 100,
        "Fwd IAT Total": 2100, "Fwd IAT Mean": 700, "Fwd IAT Std": math.sqrt(480000),
        "Fwd IAT Max": 1500, "Fwd IAT Min": 300,
        "Bwd IAT Total": 1400, "Bwd IAT Mean": 700, "Bwd IAT Std": 400 / math.sqrt(2),
        "Bwd IAT Max": 900, "Bwd IAT Min": 500,
        "Fwd PSH Flags": 0,  # pierwszy pakiet to SYN
        "Fwd Header Length": 92, "Bwd Header Length": 72,
        "Fwd Packets/s": 4 / 0.0021, "Bwd Packets/s": 3 / 0.0021,
        "Packet Length Min": 0, "Packet Length Max": 1000,
        # ładunki z podwójnym pierwszym pakietem: [0, 0, 0, 0, 100, 1000, 500, 0]
        "Packet Length Mean": 200, "Packet Length Std": math.sqrt(940000 / 7),
        "Packet Length Variance": 940000 / 7,
        "FIN Flag Count": 1, "SYN Flag Count": 2, "RST Flag Count": 0,
        "PSH Flag Count": 2, "ACK Flag Count": 6,
        "Down/Up Ratio": 0, "Average Packet Size": 1600 / 7,
        "Fwd Segment Size Avg": 25, "Bwd Segment Size Avg": 500,
        "Bwd Packet/Bulk Avg": 0, "Bwd Bulk Rate Avg": 0,  # tylko 3 pakiety z ładunkiem
        "Subflow Fwd Packets": 0, "Subflow Fwd Bytes": 14, "Subflow Bwd Bytes": 214,
        "Fwd Act Data Pkts": 1,
    }
    assert set(f) == set(expected)
    for k, v in expected.items():
        assert f[k] == pytest.approx(v), k


def test_feature_names_match_models_metadata():
    import json
    from pathlib import Path
    meta = json.loads((Path(__file__).resolve().parents[1] / "models" / "metadata.json")
                      .read_text(encoding="utf-8"))
    assert list(flow_features(tcp_flow(), +1, 6)) == meta["features"]


def test_bulk_ignores_direction_and_idle_gap():
    t = 5_000_000
    pk = [Packet(t, 100, +1, 8, 0), Packet(t + 10, 200, -1, 8, 0),
          Packet(t + 20, 100, +1, 8, 0), Packet(t + 30, 200, -1, 8, 0),
          Packet(t + 40, 100, +1, 8, 0),
          Packet(t + 2_000_040, 50, -1, 8, 0),  # > 1 s przerwy: nowy kandydat na bulk
          Packet(t + 2_000_050, 0, +1, 8, 0)]   # pusty ładunek: pomijany
    f = flow_features(Packets.of(pk), +1, 17)
    # bulk: 4 pakiety (600 B, 30 µs) + 1 kontynuacja (100 B, 10 µs)
    assert f["Bwd Packet/Bulk Avg"] == 5
    assert f["Bwd Bulk Rate Avg"] == int(700 / 40e-6)
    assert f["Fwd Header Length"] == 32 and f["Bwd Header Length"] == 24
    assert f["SYN Flag Count"] == 0 and f["Down/Up Ratio"] == 0  # 3 // 4


def test_first_packet_counted_twice_and_fwd_psh():
    pk = [Packet(T0, 10, -1, 20, PSH | ACK), Packet(T0 + 50, 30, +1, 20, ACK),
          Packet(T0 + 80, 5, -1, 20, PSH | ACK)]
    f = flow_features(Packets.of(pk), -1, 6)  # pierwszy pakiet ma znak -1, więc to on wyznacza „Fwd”
    assert f["Total Fwd Packet"] == 2 and f["Total Length of Fwd Packet"] == 15
    assert f["Fwd PSH Flags"] == 1  # PSH tylko z pierwszego pakietu, nie licznik
    assert f["Average Packet Size"] == pytest.approx((45 + 10) / 3)
    assert f["Packet Length Mean"] == pytest.approx(55 / 4)  # [10, 10, 30, 5]
    vals = [10, 10, 30, 5]
    m = sum(vals) / 4
    assert f["Packet Length Variance"] == pytest.approx(sum((v - m) ** 2 for v in vals) / 3)
    assert f["Down/Up Ratio"] == 0 and f["Subflow Fwd Bytes"] == 15 // 3


def test_zero_duration_gives_inf_rate():
    f = flow_features(Packets.of([Packet(T0, 10, +1, 8, 0), Packet(T0, 20, -1, 8, 0)]), +1, 17)
    assert math.isinf(f["Flow Bytes/s"]) and f["Flow IAT Mean"] == 0


def test_split_on_timeout_keeps_direction_and_fin_closes():
    s = 1_000_000
    pk = [Packet(T0, 0, +1, 20, ACK),
          Packet(T0 + 60 * s, 10, -1, 20, ACK),
          Packet(T0 + 121 * s, 10, -1, 20, ACK),       # > 120 s od startu: nowy przepływ
          Packet(T0 + 130 * s, 0, +1, 20, FIN | ACK),  # FIN należy do przepływu i go kończy
          Packet(T0 + 131 * s, 0, -1, 20, ACK)]        # nowy przepływ, kierunek z tego pakietu
    flows = split_flows(Packets.of(pk), tcp=True)
    assert [(a, b) for a, b, _ in flows] == [(0, 2), (2, 4), (4, 5)]
    assert [sign for _, _, sign in flows] == [+1, +1, -1]


def test_single_packet_flow_closed_by_timeout_is_dropped():
    s = 1_000_000
    pk = [Packet(T0, 0, +1, 8, 0), Packet(T0 + 121 * s, 0, +1, 8, 0),
          Packet(T0 + 122 * s, 0, -1, 8, 0)]
    flows = split_flows(Packets.of(pk), tcp=False)
    assert [(a, b) for a, b, _ in flows] == [(1, 3)]


def test_udp_ignores_fin_bit():
    pk = [Packet(T0, 5, +1, 8, FIN), Packet(T0 + 1, 5, -1, 8, FIN)]
    assert len(split_flows(Packets.of(pk), tcp=False)) == 1


def test_flow_after_timeout_without_fwd_packets():
    """Po timeoucie kierunek zostaje ze starego przepływu, więc mogą być same pakiety Bwd."""
    pk = Packets.of([Packet(T0, 10, -1, 20, PSH | ACK), Packet(T0 + 10, 20, -1, 20, ACK)])
    f = flow_features(pk, +1, 6)
    assert f["Total Fwd Packet"] == 0 and f["Total Bwd packets"] == 2
    assert f["Down/Up Ratio"] == 0 and f["Fwd PSH Flags"] == 0
    assert f["Fwd Packet Length Max"] == 0 and f["Fwd IAT Total"] == 0
    assert f["Subflow Fwd Packets"] == 0 and f["Subflow Bwd Bytes"] == 15
