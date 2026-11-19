"""Czytnik PCAP/PCAPNG i przepływy z pakietów (etap 07, E6) na plikach zbudowanych w teście."""
import socket
from collections import Counter

import dpkt
import pytest

from cic_features import ACK, FIN, PSH, SYN
from pcap_flows import (LINKTYPE_ETHERNET, LINKTYPE_RAW, connection_key, decode_packet,
                        file_flows, iter_packets)

A, B = "10.0.0.2", "10.0.0.1"  # A > B jako tekst: pierwszy pakiet A→B ma znak -1 w kluczu


def tcp_ip(src, dst, sport, dport, flags, payload=b"", opts=b""):
    tcp = dpkt.tcp.TCP(sport=sport, dport=dport, flags=flags, data=payload, opts=opts)
    tcp.off = 5 + len(opts) // 4
    return dpkt.ip.IP(src=socket.inet_aton(src), dst=socket.inet_aton(dst), p=6, data=tcp)


def udp_ip(src, dst, sport, dport, payload=b""):
    udp = dpkt.udp.UDP(sport=sport, dport=dport, data=payload)
    udp.ulen = 8 + len(payload)
    return dpkt.ip.IP(src=socket.inet_aton(src), dst=socket.inet_aton(dst), p=17, data=udp)


def ether(ip):
    return bytes(dpkt.ethernet.Ethernet(src=b"\x00" * 6, dst=b"\x01" * 6, type=0x0800, data=ip))


def write(path, frames, linktype=LINKTYPE_ETHERNET, ng=False):
    with path.open("wb") as fh:
        w = (dpkt.pcapng.Writer if ng else dpkt.pcap.Writer)(fh, linktype=linktype)
        for ts, buf in frames:
            w.writepkt(buf, ts=ts)
    return path


def tcp_session():
    """Handshake A→B, 100 B od A, 300 B od B, FIN od A; nagłówek SYN z 12 B opcji."""
    return [
        (100.0, tcp_ip(A, B, 5000, 443, SYN, opts=b"\x01" * 12)),
        (100.1, tcp_ip(B, A, 443, 5000, SYN | ACK, opts=b"\x01" * 12)),
        (100.2, tcp_ip(A, B, 5000, 443, ACK)),
        (100.5, tcp_ip(A, B, 5000, 443, PSH | ACK, b"a" * 100)),
        (101.0, tcp_ip(B, A, 443, 5000, PSH | ACK, b"b" * 300)),
        (101.5, tcp_ip(A, B, 5000, 443, FIN | ACK)),
    ]


def test_decode_tcp_fields():
    st = Counter()
    p = decode_packet(1.25, ether(tcp_ip(A, B, 5000, 443, SYN, b"x" * 7, b"\x01" * 12)),
                      LINKTYPE_ETHERNET, st)
    assert (p.ts_us, p.src, p.sport, p.dst, p.dport, p.proto) == (1_250_000, A, 5000, B, 443, 6)
    assert (p.payload, p.header, p.flags) == (7, 32, SYN)
    assert not st


def test_decode_udp_and_raw_ip():
    p = decode_packet(2.0, bytes(udp_ip(A, B, 4000, 5060, b"v" * 160)), LINKTYPE_RAW, Counter())
    assert (p.proto, p.payload, p.header, p.flags) == (17, 160, 8, 0)


def test_decode_skips_and_counts():
    st = Counter()
    icmp = dpkt.ip.IP(src=socket.inet_aton(A), dst=socket.inet_aton(B), p=1,
                      data=dpkt.icmp.ICMP(type=8, data=b"ping"))
    frag = tcp_ip(A, B, 1, 2, ACK, b"z" * 10)
    frag.mf = 1
    ipv6 = dpkt.ethernet.Ethernet(src=b"\x00" * 6, dst=b"\x01" * 6, type=0x86DD,
                                  data=dpkt.ip6.IP6(nxt=59, hlim=1, src=b"\x00" * 16,
                                                    dst=b"\x00" * 16))
    assert decode_packet(0, ether(icmp), LINKTYPE_ETHERNET, st) is None
    assert decode_packet(0, ether(frag), LINKTYPE_ETHERNET, st) is None
    assert decode_packet(0, bytes(ipv6), LINKTYPE_ETHERNET, st) is None
    assert decode_packet(0, b"\x60" + b"\x00" * 39, LINKTYPE_RAW, st) is None
    assert st == Counter(not_tcp_udp=1, fragment=1, not_ipv4=2)


def test_ip_len_zero_uses_captured_length():
    """TSO na hoście nagrywającym zostawia w nagłówku IP długość 0."""
    buf = bytearray(bytes(tcp_ip(A, B, 5000, 443, ACK, b"q" * 50)))
    buf[2:4] = b"\x00\x00"  # pole Total Length nagłówka IP
    st = Counter()
    p = decode_packet(0, bytes(buf), LINKTYPE_RAW, st)
    assert p.payload == 50 and st["ip_len_zero"] == 1


def test_unsupported_linktype_raises():
    with pytest.raises(ValueError, match="typ łącza"):
        decode_packet(0, b"\x45", 113, Counter())


def test_connection_key_is_direction_independent():
    st = Counter()
    p1 = decode_packet(0, ether(tcp_ip(A, B, 5000, 443, ACK)), LINKTYPE_ETHERNET, st)
    p2 = decode_packet(0, ether(tcp_ip(B, A, 443, 5000, ACK)), LINKTYPE_ETHERNET, st)
    (k1, s1), (k2, s2) = connection_key(p1), connection_key(p2)
    assert k1 == k2 == (6, B, 443, A, 5000) and (s1, s2) == (-1, 1)


@pytest.mark.parametrize("ng", [False, True])
def test_file_flows_tcp_session(tmp_path, ng):
    path = write(tmp_path / "x.pcap", [(t, ether(ip)) for t, ip in tcp_session()], ng=ng)
    df, st = file_flows(path, "dir/x.pcap")
    assert st["frames"] == st["packets"] == 6 and st["flows"] == 1
    f = df.iloc[0]
    # kierunek Fwd od pierwszego pakietu (A→B), mimo że A jest „większym” punktem w kluczu
    assert (f["Src IP"], f["Src Port"], f["Dst IP"], f["Dst Port"]) == (A, 5000, B, 443)
    assert f["source_file"] == "dir/x.pcap" and f["ts_us"] == 100_000_000 and f["n_packets"] == 6
    assert (f["Total Fwd Packet"], f["Total Bwd packets"]) == (4, 2)
    assert (f["Total Length of Fwd Packet"], f["Total Length of Bwd Packet"]) == (100, 300)
    assert f["Fwd Header Length"] == 32 + 20 * 3 and f["Bwd Header Length"] == 32 + 20
    assert f["Flow Duration"] == 1_500_000 and f["FIN Flag Count"] == 1


def test_format_detected_by_content_not_extension(tmp_path):
    """W ISCX jest plik .pcap, który w środku jest PCAPNG."""
    path = write(tmp_path / "ng_inside.pcap", [(1.0, bytes(udp_ip(A, B, 1, 2, b"u")))],
                 linktype=LINKTYPE_RAW, ng=True)
    assert [p.payload for p in iter_packets(path, Counter())] == [1]


def test_unknown_format_raises(tmp_path):
    path = tmp_path / "bad.pcap"
    path.write_bytes(b"NOTAPCAPFILE")
    with pytest.raises(ValueError, match="format"):
        list(iter_packets(path, Counter()))


def test_udp_connections_split_by_endpoint_pair(tmp_path):
    frames = [(1.0, ether(udp_ip(A, B, 4000, 5060, b"v" * 20))),
              (1.02, ether(udp_ip(B, A, 5060, 4000, b"v" * 20))),
              (1.04, ether(udp_ip(A, "10.0.0.9", 4000, 5060, b"v" * 20))),
              (1.06, ether(udp_ip("10.0.0.9", A, 5060, 4000, b"v" * 20)))]
    df, st = file_flows(write(tmp_path / "u.pcap", frames), "u.pcap")
    assert st["connections"] == 2 and sorted(df["Dst IP"]) == [B, "10.0.0.9"]
    assert (df["Protocol"] == 17).all() and (df["Fwd Header Length"] == 8).all()
