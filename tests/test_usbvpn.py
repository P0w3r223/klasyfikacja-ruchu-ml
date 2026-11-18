"""USBVPN2022 → przepływy CICFlowMeter (etap 06, E7): czytanie, pakiety, filtr, scalanie."""
import hashlib
import io
import json
import zipfile

import pytest

import usbvpn
from cic_features import ACK, FIN, PSH, SYN


def pkt(ts: str, b: int, flags: str | None = None, tcp_hdr: int | None = 32,
        packets: int = 1) -> dict:
    """Wpis x_packets w formacie USBVPN2022 (wszystkie wartości jako tekst)."""
    p = {"bytes": str(b), "packets": str(packets), "timestamp_start": ts, "timestamp_end": ts}
    if packets == 1:
        p["ip_header_len"] = "20"
        if flags is not None:
            p |= {"tcp_flags": flags, "tcp_header_len": str(tcp_hdr),
                  "tcp_seq_number": "1", "tcp_ack_number": "1"}
    return p


def test_iter_json_array_across_small_chunks():
    data = [{"a": i, "x_packets": [{"bytes": str(i) * 50}]} for i in range(20)]
    raw = json.dumps(data, indent=2).encode()
    out = list(usbvpn.iter_json_array(io.BytesIO(raw), chunk=7))
    assert out == data
    assert list(usbvpn.iter_json_array(io.BytesIO(b"[]"))) == []


def test_parse_ts_us():
    a = usbvpn.parse_ts_us("2022-10-17 12:32:55.289904")
    b = usbvpn.parse_ts_us("2022-10-17 12:32:56.000001")
    assert b - a == 710_097


def test_record_packets_tcp_payload_flags_and_sign():
    rec = {"ip_proto": "tcp", "port_src": 443, "port_dst": 52068, "x_packets": [
        pkt("2022-10-17 12:00:00.000000", 1452, "011000", 32),  # 1400 B, PSH+ACK
        pkt("2022-10-17 12:00:00.000010", -52, "010000", 32),   # czysty ACK wstecz
        pkt("2022-10-17 12:00:00.000020", -40, "010001", 20),   # FIN+ACK
        pkt("2022-10-17 12:00:00.000030", 144, packets=2),       # 2 × 72 B, bez nagłówków
    ]}
    pk, st = usbvpn.record_packets(rec)
    assert pk.payload.tolist() == [1400, 0, 0, 72 - 20 - 20, 72 - 20 - 20]
    assert pk.sign.tolist() == [1, -1, -1, 1, 1]
    assert pk.flags.tolist() == [PSH | ACK, ACK, FIN | ACK, ACK, ACK]
    assert pk.header.tolist() == [32, 32, 20, 20, 20]  # nagłówek TCP z poprzedniego pakietu
    assert pk.ts[3] == pk.ts[4] and st["multi"] == 1 and st["entries"] == 4


def test_record_packets_udp_uneven_multi():
    rec = {"ip_proto": "udp", "port_src": 52698, "port_dst": 443, "x_packets": [
        pkt("2022-10-17 12:00:00.000000", 464),
        pkt("2022-10-17 12:00:00.000001", -932, packets=2)]}
    pk, _ = usbvpn.record_packets(rec)
    assert pk.payload.tolist() == [436, 438, 438]  # 932 = 466 + 466; −20 IP −8 UDP
    assert pk.header.tolist() == [8, 8, 8] and pk.flags.tolist() == [0, 0, 0]
    assert pk.sign.tolist() == [1, -1, -1]


@pytest.mark.parametrize("proto,src,dst,reason", [
    ("tcp", 50000, 443, ""), ("udp", 33851, 3478, ""),
    ("gre", 0, 0, "protokół inny niż TCP/UDP"), ("icmp", 0, 2048, "protokół inny niż TCP/UDP"),
    ("udp", 52698, 9000, "infrastruktura UDP/9000"), ("tcp", 8291, 10908, "infrastruktura TCP/8291 (Winbox)"),
    ("udp", 13231, 13231, "infrastruktura UDP/13231 (WireGuard MikroTik)"),
    ("tcp", 40000, 10443, "infrastruktura TCP/10443"), ("udp", 40000, 53, "DNS"),
    ("udp", 123, 123, "NTP"), ("tcp", 9000, 40000, ""),  # UDP/9000, nie TCP
])
def test_filter_reason(proto, src, dst, reason):
    assert usbvpn.filter_reason(proto, src, dst) == reason


def test_connection_key_orients_both_directions():
    k1, m1 = usbvpn.connection_key({"ip_proto": "tcp", "port_src": 443, "port_dst": 50000})
    k2, m2 = usbvpn.connection_key({"ip_proto": "tcp", "port_src": 50000, "port_dst": 443})
    assert k1 == k2 == ("tcp", 443, 50000) and (m1, m2) == (1, -1)


def make_zip(path, members: dict[str, list[dict]]):
    with zipfile.ZipFile(path, "w") as z:
        for name, recs in members.items():
            z.writestr(name, json.dumps(recs, indent=2))


def test_build_file_merges_records_and_filters(tmp_path):
    t = "2022-10-17 12:00:{:02d}.{:06d}"
    # jedno połączenie TCP w dwóch rekordach pmacct (drugi zapisany odwrotnie i wcześniej w pliku)
    rec_late = {"ip_proto": "tcp", "port_src": 50000, "port_dst": 443, "x_packets": [
        pkt(t.format(1, 0), 540, "011000", 20),
        pkt(t.format(1, 500), 40, "010001", 20)]}                 # FIN od klienta kończy przepływ
    rec_early = {"ip_proto": "tcp", "port_src": 443, "port_dst": 50000, "x_packets": [
        pkt(t.format(0, 0), -60, "000010", 40),                   # SYN od klienta (znak −)
        pkt(t.format(0, 100), 60, "010010", 40),                  # SYN+ACK od serwera
        pkt(t.format(0, 300), 1040, "011000", 20)]}
    gre = {"ip_proto": "gre", "port_src": 0, "port_dst": 0, "x_packets": [pkt(t.format(0, 1), 100)]}
    zpath = tmp_path / "a.zip"
    make_zip(zpath, {"x/meet.json": [rec_late, gre, rec_early]})
    res = usbvpn.build_file("x/meet.json", "VoIP", zpath)
    assert res.removed == {"protokół inny niż TCP/UDP": 1}
    assert res.stats["connections"] == 1 and res.stats["records_merged"] == 1
    assert len(res.flows) == 1
    f = res.flows.iloc[0]
    assert (f["Src Port"], f["Dst Port"]) == (50000, 443)  # „Fwd” = klient, autor SYN
    assert f["Total Fwd Packet"] == 3 and f["Total Bwd packets"] == 2
    assert f["Total Length of Fwd Packet"] == 500 and f["Total Length of Bwd Packet"] == 1000
    assert f["SYN Flag Count"] == 2 and f["FIN Flag Count"] == 1
    assert f["Fwd Header Length"] == 80 and f["Flow Duration"] == 1_000_500
    assert list(res.flows.columns[5:]) == usbvpn.FEATURES


def test_clean_drops_inf_and_duplicates():
    import pandas as pd
    row = dict.fromkeys(usbvpn.FEATURES, 1.0) | {"service": "WWW"}
    df = pd.DataFrame([row, row, row | {"Flow Bytes/s": float("inf")}])
    out, st = usbvpn.clean(df)
    assert len(out) == 1 and st == {"invalid": 1, "duplicates": 1}


def test_download_checks_md5(tmp_path):
    src = tmp_path / "src.zip"
    src.write_bytes(b"abc")
    md5 = hashlib.md5(b"abc").hexdigest()
    out = usbvpn.download(tmp_path / "dl", url=src.as_uri(), md5=md5)
    assert out.read_bytes() == b"abc"
    with pytest.raises(ValueError, match="MD5"):
        usbvpn.download(tmp_path / "dl", url=src.as_uri(), md5="0" * 32)


def test_split_merged_segments_to_mss():
    t = "2022-10-17 12:00:00.{:06d}"
    rec = {"ip_proto": "tcp", "port_src": 443, "port_dst": 50000, "x_packets": [
        pkt(t.format(0), 1452, "010000", 32),        # 1400 B: MSS kierunku +
        pkt(t.format(10), 11252, "011000", 32),      # 11200 B = 8 × 1400, PSH+ACK
        pkt(t.format(20), 3052, "011001", 32),       # 3000 B = 2 × 1400 + 200, FIN na końcu
        pkt(t.format(30), -3040, "011000", 20),      # kierunek − bez pakietów w MTU: MSS 1460
    ]}
    pk, st = usbvpn.record_packets(rec)
    pl, fl = pk.payload.tolist(), pk.flags.tolist()
    assert pl == [1400] + [1400] * 8 + [1400, 1400, 200] + [1460, 1460, 80]
    assert fl[1:9] == [ACK] * 7 + [PSH | ACK]          # PSH tylko na ostatnim segmencie
    assert fl[9:12] == [ACK, ACK, PSH | ACK | FIN]
    assert pk.ts[1:9].tolist() == [pk.ts[1]] * 8 and pk.header[1:9].tolist() == [32] * 8
    assert st["merged"] == 3 and st["merged_segments"] == 8 + 3 + 3
    raw, _ = usbvpn.record_packets(rec, split_offload=False)
    assert raw.payload.tolist() == [1400, 11200, 3000, 3000]


def test_udp_is_never_split():
    rec = {"ip_proto": "udp", "port_src": 1, "port_dst": 443,
           "x_packets": [pkt("2022-10-17 12:00:00.000000", 1600)]}
    pk, st = usbvpn.record_packets(rec)
    assert pk.payload.tolist() == [1572] and st["merged"] == 0
