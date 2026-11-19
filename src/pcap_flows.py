"""Przepływy CICFlowMeter z plików PCAP i PCAPNG (E6, ISCX VPN-nonVPN 2016).

Pakiety czyta dpkt; cechy i granice przepływów liczy `cic_features` (te same definicje co w E7,
sprawdzone na Darknet). Różnice względem E7 (USBVPN2022):
- są adresy IP, więc połączenie to (protokół, para punktów końcowych IP:port);
- scalonych segmentów TCP nie rozbijamy: CICFlowMeter liczył Darknet z tych samych PCAP-ów,
  więc widział te same pakiety (Darknet Video VPN-nonVPN ma 8,8% przepływów z ładunkiem
  > 1460 B, decyzje.md, wpis E7 krok 1).

Format pliku rozpoznajemy po pierwszych bajtach, nie po rozszerzeniu (w ISCX jest plik `.pcap`,
który w środku jest PCAPNG).
"""
import socket
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import dpkt
import numpy as np
import pandas as pd

from cic_features import Packets, flow_features, split_flows

PCAPNG_MAGIC = b"\x0a\x0d\x0d\x0a"
PCAP_MAGICS = {b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4", b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d"}
LINKTYPE_ETHERNET = 1
LINKTYPE_RAW = 101  # pakiet IP bez ramki (nagranie z interfejsu tunelu VPN)
TCP, UDP = 6, 17
UDP_HEADER = 8
META_COLS = ["source_file", "Src IP", "Src Port", "Dst IP", "Dst Port", "ts_us", "n_packets"]


@dataclass(frozen=True)
class RawPacket:
    ts_us: int
    src: str
    sport: int
    dst: str
    dport: int
    proto: int
    payload: int  # B ładunku TCP/UDP
    header: int  # B nagłówka TCP/UDP
    flags: int  # flagi TCP, 0 dla UDP


def open_reader(fh: BinaryIO) -> dpkt.pcap.Reader | dpkt.pcapng.Reader:
    magic = fh.read(4)
    fh.seek(0)
    if magic == PCAPNG_MAGIC:
        return dpkt.pcapng.Reader(fh)
    if magic in PCAP_MAGICS:
        return dpkt.pcap.Reader(fh)
    raise ValueError(f"nieznany format pliku (pierwsze bajty {magic.hex()}), oczekiwano PCAP/PCAPNG")


def _ip_layer(buf: bytes, linktype: int) -> object:
    if linktype == LINKTYPE_ETHERNET:
        return dpkt.ethernet.Ethernet(buf).data
    if linktype == LINKTYPE_RAW:
        version = buf[0] >> 4 if buf else 0
        return dpkt.ip.IP(buf) if version == 4 else None
    raise ValueError(f"nieobsługiwany typ łącza {linktype} (obsługiwane: Ethernet 1, raw IP 101)")


def decode_packet(ts: float, buf: bytes, linktype: int, stats: Counter) -> RawPacket | None:
    """Pakiet IPv4 TCP/UDP albo None; powód pominięcia trafia do `stats`."""
    try:
        ip = _ip_layer(buf, linktype)
    except (dpkt.UnpackError, IndexError):
        stats["decode_error"] += 1
        return None
    if not isinstance(ip, dpkt.ip.IP):
        stats["not_ipv4"] += 1
        return None
    if ip.p not in (TCP, UDP):
        stats["not_tcp_udp"] += 1
        return None
    if ip.mf or ip.offset:
        stats["fragment"] += 1
        return None
    l4 = ip.data
    if not isinstance(l4, (dpkt.tcp.TCP, dpkt.udp.UDP)):
        stats["decode_error"] += 1
        return None
    header, flags = (l4.off * 4, l4.flags) if ip.p == TCP else (UDP_HEADER, 0)
    ip_len = ip.len
    if ip_len == 0:  # TSO na hoście nagrywającym: długość z przechwyconych bajtów
        stats["ip_len_zero"] += 1
        ip_len = len(ip)
    payload = ip_len - ip.hl * 4 - header
    if payload < 0:
        stats["neg_payload"] += 1
        payload = 0
    return RawPacket(round(ts * 1_000_000), socket.inet_ntoa(ip.src), l4.sport,
                     socket.inet_ntoa(ip.dst), l4.dport, ip.p, payload, header, flags)


def iter_packets(path: Path, stats: Counter) -> Iterator[RawPacket]:
    with path.open("rb") as fh:
        reader = open_reader(fh)
        linktype = reader.datalink()
        for ts, buf in reader:
            stats["frames"] += 1
            pkt = decode_packet(ts, buf, linktype, stats)
            if pkt is not None:
                stats["packets"] += 1
                yield pkt


def connection_key(p: RawPacket) -> tuple[tuple[int, str, int, str, int], int]:
    """Klucz (protokół, mniejszy punkt końcowy, większy) i znak kierunku pakietu w tym układzie."""
    a, b = (p.src, p.sport), (p.dst, p.dport)
    if a <= b:
        return (p.proto, *a, *b), 1
    return (p.proto, *b, *a), -1


def group_connections(packets: Iterable[RawPacket]) -> dict[tuple, Packets]:
    rows: dict[tuple, list[tuple[int, int, int, int, int]]] = defaultdict(list)
    for p in packets:
        key, sign = connection_key(p)
        rows[key].append((p.ts_us, p.payload, sign, p.header, p.flags))
    conns = {}
    for key, r in rows.items():
        pk = Packets.of(r)
        conns[key] = pk[np.argsort(pk.ts, kind="stable")]
    return conns


def connection_flows(key: tuple, pk: Packets) -> list[dict]:
    """Przepływy CICFlowMeter jednego połączenia: kolumny meta (bez source_file) i 55 cech."""
    proto, ip_a, port_a, ip_b, port_b = key
    out = []
    for start, end, fsign in split_flows(pk, tcp=proto == TCP):
        src, dst = ((ip_a, port_a), (ip_b, port_b)) if fsign == 1 else ((ip_b, port_b), (ip_a, port_a))
        out.append({"Src IP": src[0], "Src Port": src[1], "Dst IP": dst[0], "Dst Port": dst[1],
                    "ts_us": int(pk.ts[start]), "n_packets": end - start,
                    **flow_features(pk[start:end], fsign, proto)})
    return out


def file_flows(path: Path, source_file: str) -> tuple[pd.DataFrame, Counter]:
    """Wszystkie przepływy z jednego pliku i liczniki pominiętych ramek."""
    stats: Counter = Counter()
    conns = group_connections(iter_packets(path, stats))
    rows = [{"source_file": source_file, **f}
            for key, pk in conns.items() for f in connection_flows(key, pk)]
    stats["connections"] = len(conns)
    stats["flows"] = len(rows)
    return pd.DataFrame(rows), stats
