"""Testy logiki przygotowania danych (src/preprocess.py) na małych ramkach."""
import numpy as np
import pandas as pd
import pytest

from preprocess import (
    assign_sessions,
    background_reason,
    drop_invalid_and_duplicates,
    is_multicast_or_broadcast,
)

T0 = pd.Timestamp("2015-02-23 10:00:00")


# --- adresy multicast/broadcast ---------------------------------------------

@pytest.mark.parametrize("ip", [
    "224.0.0.252",       # LLMNR
    "239.255.255.250",   # SSDP
    "255.255.255.255",
    "192.168.1.255",     # broadcast podsieci /24
    "ff02::1",           # multicast IPv6
    "not-an-ip",         # niepoprawny adres traktujemy jak ruch do usunięcia
])
def test_multicast_or_broadcast_detected(ip):
    assert is_multicast_or_broadcast(ip)


@pytest.mark.parametrize("ip", ["10.0.0.1", "131.202.240.150", "192.168.1.254", "fe80::1"])
def test_unicast_kept(ip):
    assert not is_multicast_or_broadcast(ip)


@pytest.mark.parametrize("ip", ["173.194.115.255", "54.145.236.255"])
def test_dot255_known_false_positive_kept_for_v1_reproducibility(ip):
    # Zwykłe hosty (TCP Video), które reguła .255 błędnie usuwa. Zostawione świadomie,
    # żeby data-processed-v1 był odtwarzalny; patrz decyzje.md (etap 02).
    assert is_multicast_or_broadcast(ip)


# --- ruch tła ---------------------------------------------------------------

def flows(*rows):
    return pd.DataFrame(rows, columns=["Protocol", "Src Port", "Dst Port", "Dst IP"])


@pytest.mark.parametrize("port, name", [
    (53, "DNS"), (5353, "mDNS"), (5355, "LLMNR"), (137, "NetBIOS"), (138, "NetBIOS"),
    (139, "NetBIOS"), (1900, "SSDP"), (67, "DHCP"), (68, "DHCP"), (123, "NTP"),
    (161, "SNMP"), (162, "SNMP"), (17500, "Dropbox LAN sync"),
])
def test_background_port_on_either_side(port, name):
    df = flows((17, 50000, port, "10.0.0.1"), (17, port, 50000, "10.0.0.1"))
    assert background_reason(df).tolist() == [name, name]


def test_non_tcp_udp_protocol_removed():
    df = flows((1, 0, 0, "10.0.0.1"), (0, 0, 0, "10.0.0.1"))
    assert background_reason(df).tolist() == ["protokół inny niż TCP/UDP"] * 2


def test_multicast_destination_removed():
    df = flows((17, 50000, 50001, "224.0.0.1"))
    assert background_reason(df).tolist() == ["multicast/broadcast"]


def test_regular_flows_kept():
    df = flows((6, 50000, 443, "10.0.0.1"), (17, 50000, 3478, "131.202.240.150"))
    assert background_reason(df).tolist() == ["", ""]


def test_reason_precedence_protocol_then_dst_then_src_then_address():
    df = flows(
        (1, 137, 53, "224.0.0.1"),    # protokół wygrywa ze wszystkim
        (17, 137, 53, "224.0.0.1"),   # port docelowy przed źródłowym
        (17, 137, 50000, "224.0.0.1"),  # port przed adresem
    )
    assert background_reason(df).tolist() == ["protokół inny niż TCP/UDP", "DNS", "NetBIOS"]


def test_background_reason_keeps_index():
    df = flows((6, 50000, 443, "10.0.0.1"), (17, 50000, 53, "10.0.0.1"))
    df.index = [10, 20]
    assert background_reason(df).to_dict() == {10: "", 20: "DNS"}


# --- sesje ------------------------------------------------------------------

def session_frame(*rows):
    """Wiersze: (Src IP, Dst IP, traffic_type, service, minuty od T0)."""
    df = pd.DataFrame(rows, columns=["Src IP", "Dst IP", "traffic_type", "service", "minutes"])
    df["ts"] = T0 + pd.to_timedelta(df.pop("minutes"), unit="min")
    return df


def test_gap_of_exactly_five_minutes_stays_in_session():
    df = session_frame(("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 0),
                       ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 5))
    s = assign_sessions(df, gap_min=5)
    assert s.iloc[0] == s.iloc[1]


def test_gap_just_over_five_minutes_starts_new_session():
    df = session_frame(("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 0),
                       ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 0))
    df.loc[1, "ts"] = T0 + pd.Timedelta(minutes=5, seconds=1)
    s = assign_sessions(df, gap_min=5)
    assert s.iloc[0] != s.iloc[1]


def test_gap_is_measured_between_consecutive_flows():
    # Cały łańcuch trwa 12 min, ale żadna przerwa nie przekracza 5 min.
    df = session_frame(*[("10.0.0.1", "10.0.0.2", "VPN", "VoIP", m) for m in (0, 4, 8, 12)])
    assert assign_sessions(df, gap_min=5).nunique() == 1


def test_reversed_ip_pair_is_same_session():
    df = session_frame(("10.0.0.1", "10.0.0.2", "NonVPN", "Video", 0),
                       ("10.0.0.2", "10.0.0.1", "NonVPN", "Video", 1))
    s = assign_sessions(df, gap_min=5)
    assert s.iloc[0] == s.iloc[1]


@pytest.mark.parametrize("other", [
    ("10.0.0.1", "10.0.0.2", "NonVPN", "VoIP", 1),   # inna usługa
    ("10.0.0.1", "10.0.0.2", "VPN", "Video", 1),     # inny typ ruchu
    ("10.0.0.1", "10.0.0.3", "NonVPN", "Video", 1),  # inna para IP
])
def test_different_label_or_pair_is_different_session(other):
    df = session_frame(("10.0.0.1", "10.0.0.2", "NonVPN", "Video", 0), other)
    s = assign_sessions(df, gap_min=5)
    assert s.iloc[0] != s.iloc[1]


def test_unsorted_input_is_aligned_to_original_index():
    df = session_frame(
        ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 20),  # druga sesja
        ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 0),   # pierwsza sesja
        ("10.0.0.2", "10.0.0.1", "VPN", "VoIP", 22),  # druga sesja, odwrócona para
        ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 3),   # pierwsza sesja
    )
    df.index = [7, 3, 9, 1]
    s = assign_sessions(df, gap_min=5)
    assert s.index.tolist() == [7, 3, 9, 1]
    assert s[3] == s[1] != s[7] == s[9]


def test_gap_threshold_is_configurable():
    df = session_frame(("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 0),
                       ("10.0.0.1", "10.0.0.2", "VPN", "VoIP", 3))
    assert assign_sessions(df, gap_min=5).nunique() == 1
    assert assign_sessions(df, gap_min=1).nunique() == 2


# --- czyszczenie ------------------------------------------------------------

def labelled(rows):
    return pd.DataFrame(rows, columns=["f1", "f2", "traffic_type", "service"])


def test_invalid_rows_removed():
    df = labelled([
        (1.0, 2.0, "VPN", "VoIP"),
        (np.inf, 2.0, "VPN", "VoIP"),
        (1.0, np.nan, "VPN", "VoIP"),
        ("abc", 2.0, "VPN", "VoIP"),
    ])
    clean, stats = drop_invalid_and_duplicates(df, ["f1", "f2"])
    assert clean.index.tolist() == [0]
    assert stats["invalid"] == 3


def test_duplicates_with_same_labels_removed_first_kept():
    df = labelled([
        (1.0, 2.0, "VPN", "VoIP"),
        (1.0, 2.0, "VPN", "VoIP"),
        (1.0, 3.0, "VPN", "VoIP"),
    ])
    clean, stats = drop_invalid_and_duplicates(df, ["f1", "f2"])
    assert clean.index.tolist() == [0, 2]
    assert stats["duplicates"] == 1
    assert stats["conflicts"] == 0


def test_same_features_with_different_labels_kept_and_counted():
    df = labelled([
        (1.0, 2.0, "VPN", "VoIP"),
        (1.0, 2.0, "VPN", "Video"),
        (1.0, 2.0, "NonVPN", "VoIP"),
    ])
    clean, stats = drop_invalid_and_duplicates(df, ["f1", "f2"])
    assert len(clean) == 3
    assert stats == {"invalid": 0, "duplicates": 0, "conflicts": 3}


def test_input_frame_not_modified():
    df = labelled([(1.0, 2.0, "VPN", "VoIP"), (1.0, 2.0, "VPN", "VoIP")])
    before = df.copy()
    drop_invalid_and_duplicates(df, ["f1", "f2"])
    pd.testing.assert_frame_equal(df, before)
