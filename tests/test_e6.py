"""Dopasowanie etykiet Darknet.CSV do przepływów z PCAP-ów i cechy z pierwszych N pakietów
(etap 07, E6)."""
import pandas as pd
import pytest

from cic_features import Packets
from e6 import (DARKNET_UTC_OFFSET, FLOW_ID, FULL_FLOW, MATCH_TOLERANCE, candidates, clean_e6,
                coverage_table, feature_agreement, full_flow_mismatches, prefix_features, resolve,
                select_files)
from pcap_flows import FlowPackets
from usbvpn import FEATURES

T0 = pd.Timestamp("2015-04-29 13:47:03.600")  # UTC; w Darknet 10:47:03 (ADT)
LOCAL = (T0 + DARKNET_UTC_OFFSET).strftime("%d/%m/%Y %I:%M:%S %p")


def flow(sport, t=T0, fwd=10, bwd=5, sip="1.1.1.1"):
    return {"Src IP": sip, "Src Port": sport, "Dst IP": "2.2.2.2", "Dst Port": 5060,
            "Protocol": 17.0, "ts_us": t.value // 1000, "Total Fwd Packet": fwd,
            "Total Bwd packets": bwd, "source_file": "f.pcap"}


def dk(sport, stamp=LOCAL, label="NonVPN", service_raw="VOIP", service="VoIP", fwd=10, bwd=5):
    return {"Src IP": "1.1.1.1", "Src Port": sport, "Dst IP": "2.2.2.2", "Dst Port": 5060,
            "Protocol": 17, "Timestamp": stamp, "traffic_type": label, "service": service,
            "service_raw": service_raw, "Total Fwd Packet": fwd, "Total Bwd packets": bwd}


def darknet(rows):
    d = pd.DataFrame(rows)
    return d.assign(dts=pd.to_datetime(d["Timestamp"], format="%d/%m/%Y %I:%M:%S %p"),
                    darknet_row=d.index,
                    label=d["traffic_type"] + "|" + d["service_raw"].str.lower())


def match(flows, rows):
    f, d = pd.DataFrame(flows), darknet(rows)
    return resolve(f, candidates(f, d, DARKNET_UTC_OFFSET, MATCH_TOLERANCE))


def test_match_with_offset_and_second_truncation():
    m = match([flow(1000)], [dk(1000)])
    assert m.loc[0, "match"] == "dopasowany" and m.loc[0, "service"] == "VoIP"
    assert m.loc[0, "darknet_row"] == 0 and m.loc[0, "same_counts"]


def test_no_match_outside_tolerance_or_other_tuple():
    late = (T0 + DARKNET_UTC_OFFSET + pd.Timedelta(seconds=3)).strftime("%d/%m/%Y %I:%M:%S %p")
    m = match([flow(1000), flow(2000)], [dk(1000, stamp=late), dk(2001)])
    assert list(m["match"]) == ["brak", "brak"] and m["service"].isna().all()


def test_utc_time_without_offset_does_not_match():
    utc = T0.strftime("%d/%m/%Y %I:%M:%S %p")
    assert match([flow(1000)], [dk(1000, stamp=utc)]).loc[0, "match"] == "brak"


def test_conflicting_labels_are_ambiguous():
    m = match([flow(1000)], [dk(1000), dk(1000, service_raw="Audio-Streaming", service="Audio")])
    assert m.loc[0, "match"] == "niejednoznaczny" and pd.isna(m.loc[0, "service"])


def test_label_case_differences_are_the_same_label():
    m = match([flow(1000)], [dk(1000, service_raw="Video-Streaming", service="Video"),
                             dk(1000, service_raw="Video-streaming", service="Video")])
    assert m.loc[0, "match"] == "dopasowany"


def test_prefers_candidate_with_same_packet_counts():
    m = match([flow(1000, fwd=10, bwd=5)], [dk(1000, fwd=3, bwd=1), dk(1000, fwd=10, bwd=5)])
    assert m.loc[0, "darknet_row"] == 1 and m.loc[0, "same_counts"]


def test_one_darknet_row_keeps_one_flow():
    """To samo połączenie w dwóch plikach (np. *_a i *_b) dopasowane do jednego wiersza."""
    m = match([flow(1000, fwd=9), flow(1000)], [dk(1000)])
    assert list(m["match"]) == ["duplikat", "dopasowany"]
    assert pd.isna(m.loc[0, "darknet_row"])


def test_coverage_counts_darknet_rows_found():
    d = darknet([dk(1000), dk(2000), dk(3000, service_raw="Video-Streaming", service="Video")])
    f = pd.DataFrame([flow(1000)])
    m = resolve(f, candidates(f, d, DARKNET_UTC_OFFSET, MATCH_TOLERANCE))
    cov = coverage_table(m, d)
    assert cov.loc[("NonVPN", "VoIP"), "darknet"] == 2
    assert cov.loc[("NonVPN", "VoIP"), "dopasowane"] == 1
    assert cov.loc[("NonVPN", "Video"), "dopasowane"] == 0


def test_select_files_pattern(tmp_path):
    for name in ["NonVPN/voipbuster1b.pcapng", "NonVPN/youtube1.pcap", "NonVPN/email1a.pcap",
                 "VPN/vpn_skype_audio1.pcap", "VPN/vpn_bittorrent.pcap"]:
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_bytes(b"")
    assert [p.name for p in select_files(tmp_path)] == [
        "voipbuster1b.pcapng", "youtube1.pcap", "vpn_skype_audio1.pcap"]


def test_select_files_empty_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        select_files(tmp_path)


# --- sesja 2: cechy z pierwszych N pakietów ---

def udp_flow(sport, n, ts0=1_000_000):
    """UDP: pakiety co 10 ms naprzemiennie w obu kierunkach, ładunek rośnie z numerem pakietu."""
    pk = Packets.of([(ts0 + 10_000 * i, 100 + i, 1 if i % 2 == 0 else -1, 8, 0) for i in range(n)])
    meta = {"Src IP": "1.1.1.1", "Src Port": sport, "Dst IP": "2.2.2.2", "Dst Port": 5060,
            "ts_us": ts0, "n_packets": n}
    return FlowPackets(meta, pk, 1, 17)


def wanted_of(flows, service="VoIP"):
    rows = [{"source_file": rel, **f.meta, **f.features(), "traffic_type": "NonVPN",
             "service": service} for rel, f in flows]
    return pd.DataFrame(rows)


def test_prefix_features_first_n_and_full():
    flows = [("a.pcap", udp_flow(1000, 30)), ("a.pcap", udp_flow(1001, 3))]
    out = prefix_features(flows, wanted_of(flows), first_n=(5, 20))
    assert len(out) == 2 * 3
    long = out[out["Src Port"] == 1000].set_index("n_first")
    assert long.loc[5, "Total Fwd Packet"] + long.loc[5, "Total Bwd packets"] == 5
    assert long.loc[20, "Flow Duration"] == 19 * 10_000
    assert long.loc[FULL_FLOW, "Flow Duration"] == 29 * 10_000
    assert (out["service"] == "VoIP").all()
    assert full_flow_mismatches(out, wanted_of(flows)) == 0


def test_prefix_shorter_than_n_equals_full_flow():
    flows = [("a.pcap", udp_flow(1001, 3))]
    out = prefix_features(flows, wanted_of(flows), first_n=(5,)).set_index("n_first")
    pd.testing.assert_series_equal(out.loc[5, FEATURES], out.loc[FULL_FLOW, FEATURES],
                                   check_names=False)


def test_prefix_features_ignores_unwanted_and_requires_all_wanted():
    flows = [("a.pcap", udp_flow(1000, 10)), ("b.pcap", udp_flow(1000, 10))]
    out = prefix_features(flows, wanted_of(flows[:1]), first_n=(5,))
    assert set(out["source_file"]) == {"a.pcap"}
    with pytest.raises(ValueError, match="nie ma w PCAP"):
        prefix_features(flows[:1], wanted_of(flows), first_n=(5,))


def test_prefix_features_rejects_duplicate_keys():
    flows = [("a.pcap", udp_flow(1000, 10))]
    with pytest.raises(ValueError, match="powtórzony klucz"):
        prefix_features(flows, pd.concat([wanted_of(flows)] * 2), first_n=(5,))
    with pytest.raises(ValueError, match="dwa przepływy"):
        prefix_features(flows * 2, wanted_of(flows), first_n=(5,))


def test_full_flow_mismatch_detected():
    flows = [("a.pcap", udp_flow(1000, 10))]
    wanted = wanted_of(flows)
    out = prefix_features(flows, wanted, first_n=(5,))
    assert full_flow_mismatches(out, wanted.assign(**{"Flow Duration": 1.0})) == 1
    assert list(out.columns[:len(FLOW_ID)]) == FLOW_ID


# --- sesja 1: czyszczenie i zgodność cech (liczby z dopasowanie.md) ---

def labelled(n=4, **over):
    base = {"Src IP": "1.1.1.1", "Dst IP": "2.2.2.2", "Src Port": 40000, "Dst Port": 443,
            "match": "dopasowany", "traffic_type": "NonVPN", "service": "Video"}
    rows = []
    for i in range(n):
        feats = {f: float(i + 1) for f in FEATURES}
        feats["Protocol"] = 6.0
        rows.append({**base, "Src Port": 40000 + i, **feats, "darknet_row": i})
    return pd.DataFrame(rows).assign(**over) if over else pd.DataFrame(rows)


def test_clean_e6_drops_unmatched_other_services_background_invalid_and_duplicates():
    df = labelled(6)
    df.loc[1, "match"] = "brak"
    df.loc[2, "service"] = "Audio"
    df.loc[3, "Dst Port"] = 53  # DNS: ruch tła
    df.loc[4, "Flow Bytes/s"] = float("inf")
    dup = df.iloc[[0]].assign(**{"Src Port": 50000})  # te same cechy i etykieta
    clean, st = clean_e6(pd.concat([df, dup], ignore_index=True))
    assert list(clean["darknet_row"]) == [0, 5]
    assert st == {"voip_video": 5, "background": 1, "invalid": 1, "duplicates": 1,
                  "conflicts": 0, "final": 2}


def test_feature_agreement_counts_equal_and_close():
    clean = labelled(4)
    raw = clean[FEATURES].copy()
    raw.loc[1, "Flow Duration"] = raw.loc[1, "Flow Duration"] * 1.005  # w granicy 1%
    raw.loc[2, "Flow Duration"] = 1000.0  # daleko
    out = feature_agreement(clean, raw)
    assert out.loc["Flow Duration", "rowne"] == 0.5
    assert out.loc["Flow Duration", "w_1proc"] == 0.75
    assert out.loc["(wszystkie 55 naraz)", "rowne"] == 0.5
    assert out.loc["Total Fwd Packet", "rowne"] == 1.0
