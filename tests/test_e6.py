"""Dopasowanie etykiet Darknet.CSV do przepływów z PCAP-ów (etap 07, E6)."""
import pandas as pd
import pytest

from e6 import (DARKNET_UTC_OFFSET, MATCH_TOLERANCE, candidates, coverage_table, resolve,
                select_files)

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
