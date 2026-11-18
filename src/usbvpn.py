"""USBVPN2022 (Naas, Fesl; Zenodo 10.5281/zenodo.7301756, CC BY 4.0) do E7.

Pobranie archiwum z kontrolą MD5, strumieniowe czytanie JSON-ów prosto z zip, filtr ruchu tła
i infrastruktury, przepływy i cechy jak w CICFlowMeter (src/cic_features.py).

Użycie: python src/usbvpn.py download | build
"""
import argparse
import hashlib
import io
import json
import shutil
import urllib.request
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd

from cic_features import ACK, FIN, PSH, Packets, flow_features, split_flows
from preprocess import BACKGROUND_PORTS

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external"
ZIP_NAME = "encrypted_vpn_dataset.zip"
ZIP_URL = f"https://zenodo.org/records/7301756/files/{ZIP_NAME}?download=1"
ZIP_MD5 = "35a4aef78526440cd6e352de49c4daf2"
ARCHIVE_ROOT = "encrypted_vpn_dataset"

# Plik → usługa w pisowni projektu (mail i ssh poza zakresem).
SERVICES = {"non_streaming": "WWW", "streaming": "Video", "meet": "VoIP"}
PROTOCOLS = {"tcp": 6, "udp": 17}
INFRA_PORTS = {
    ("udp", 9000): "infrastruktura UDP/9000",
    ("udp", 13231): "infrastruktura UDP/13231 (WireGuard MikroTik)",
    ("tcp", 8291): "infrastruktura TCP/8291 (Winbox)",
    ("tcp", 10443): "infrastruktura TCP/10443",
}
IP_HEADER, UDP_HEADER = 20, 8
MTU = 1500  # pakiet IP dłuższy niż MTU Ethernetu to segmenty scalone przez kartę (GRO)
META_COLS = ["service", "source_file", "ts", "Src Port", "Dst Port"]
FEATURES = json.loads((ROOT / "models" / "metadata.json").read_text(encoding="utf-8"))["features"]
_EPOCH = datetime(1970, 1, 1)
_US = timedelta(microseconds=1)


def file_md5(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def download(dest_dir: Path = EXTERNAL, url: str = ZIP_URL, md5: str = ZIP_MD5) -> Path:
    """Pobiera archiwum (jeśli go nie ma) i sprawdza MD5; zła suma przerywa pracę."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / ZIP_NAME
    if not path.exists():
        part = path.with_suffix(".part")
        with urllib.request.urlopen(url) as resp, part.open("wb") as f:
            shutil.copyfileobj(resp, f, length=1 << 20)
        part.replace(path)
    actual = file_md5(path)
    if actual != md5:
        raise ValueError(f"{path}: MD5 {actual} różni się od Zenodo ({md5}); usuń plik "
                         "i pobierz ponownie")
    return path


def iter_json_array(stream: BinaryIO, chunk: int = 1 << 22) -> Iterator[dict]:
    """Kolejne obiekty z pliku będącego tablicą JSON, bez wczytywania całości do pamięci."""
    text = io.TextIOWrapper(stream, encoding="utf-8")
    dec = json.JSONDecoder()
    buf, pos, started = "", 0, False
    while True:
        # pomiń białe znaki, „[” na początku i przecinki między obiektami
        while True:
            while pos < len(buf) and buf[pos] in " \t\r\n,[":
                if buf[pos] == "[":
                    started = True
                pos += 1
            if pos < len(buf):
                break
            more = text.read(chunk)
            if not more:
                return
            buf, pos = more, 0
        if not started:
            raise ValueError("plik nie zaczyna się od tablicy JSON")
        if buf[pos] == "]":
            return
        while True:
            try:
                obj, end = dec.raw_decode(buf, pos)
                break
            except json.JSONDecodeError:
                more = text.read(chunk)
                if not more:
                    raise
                buf, pos = buf[pos:] + more, 0
        yield obj
        pos = end


def iter_records(member: str, zip_path: Path | None = None) -> Iterator[dict]:
    """Rekordy (przepływy pmacct) z jednego pliku JSON w archiwum, czytane prosto z zip."""
    with zipfile.ZipFile(zip_path or EXTERNAL / ZIP_NAME) as z, z.open(member) as f:
        yield from iter_json_array(f)


def parse_ts_us(s: str) -> int:
    """„2022-10-17 12:32:55.289904” → µs od 1970-01-01 (czas lokalny nagrania, bez strefy)."""
    return (datetime.fromisoformat(s) - _EPOCH) // _US


def filter_reason(proto: str, port_src: int, port_dst: int) -> str:
    """Powód usunięcia rekordu albo „” (zostaje). Reguła ustalona przed oceną (decyzje.md, E7).

    Jak w preprocess.py: protokoły inne niż TCP/UDP i porty ruchu tła (BACKGROUND_PORTS).
    Dodatkowo infrastruktura laboratorium USBVPN2022, obecna w plikach „Non VPN”: GRE (odpada
    jako protokół), UDP/9000, UDP/13231 (WireGuard na MikroTiku), TCP/8291 (Winbox),
    TCP/10443. Adresów IP nie ma, więc reguły multicast/broadcast nie da się zastosować.
    """
    if proto not in PROTOCOLS:
        return "protokół inny niż TCP/UDP"
    for port in (port_dst, port_src):
        if port in BACKGROUND_PORTS:
            return BACKGROUND_PORTS[port]
    for port in (port_dst, port_src):
        if (proto, port) in INFRA_PORTS:
            return INFRA_PORTS[(proto, port)]
    return ""


def split_merged(rows: list[tuple[int, int, int, int, int, int]],
                 stats: dict[str, int]) -> list[tuple[int, int, int, int, int]]:
    """Rozbija scalone segmenty TCP (pakiet IP > 1500 B, GRO karty) na segmenty o długości MSS.

    MSS kierunku = największy ładunek wśród pakietów tego kierunku, które mieszczą się w MTU
    (w danych zwykle 1400 B, a scalony ładunek jest jego wielokrotnością); bez takich pakietów
    1460 B minus opcje TCP. Segmenty dostają ten sam czas (µs) i nagłówek, a PSH/FIN zostają
    tylko na ostatnim, jak przy wysyłaniu bez offloadu.
    """
    mss: dict[int, int] = {}
    for _, payload, sign, l4, _, ip_len in rows:
        if ip_len <= MTU:
            mss[sign] = max(mss.get(sign, 0), payload)
    out = []
    for ts, payload, sign, l4, flags, ip_len in rows:
        m = mss.get(sign) or (MTU - IP_HEADER - l4)
        if ip_len <= MTU or payload <= m:
            out.append((ts, payload, sign, l4, flags))
            continue
        n_seg = -(-payload // m)
        stats["merged"] += 1
        stats["merged_segments"] += n_seg
        head = flags & ~(PSH | FIN)
        out += [(ts, m, sign, l4, head)] * (n_seg - 1)
        out.append((ts, payload - m * (n_seg - 1), sign, l4, flags))
    return out


def record_packets(rec: dict, split_offload: bool = True) -> tuple[Packets, dict[str, int]]:
    """Pakiety rekordu pmacct w układzie rekordu (znak +1: port_src → port_dst).

    `bytes` to całkowita długość pakietu IP (czysty ACK: 52 = 20 IP + 32 TCP), więc
    ładunek = |bytes| - ip_header_len - nagłówek TCP (UDP: 8 B). Wpis z `packets` = k > 1 to
    k pakietów z tej samej mikrosekundy bez pól nagłówków: dzielimy bajty po równo, nagłówek IP
    20 B, nagłówek TCP z poprzedniego pakietu rekordu, flagi TCP: ACK. Scalone segmenty TCP
    rozbija `split_merged` (split_offload=False zostawia je jak w danych).
    """
    tcp = rec["ip_proto"] == "tcp"
    l4_default = 20 if tcp else UDP_HEADER
    rows: list[tuple[int, int, int, int, int, int]] = []
    stats = {"entries": 0, "multi": 0, "neg_payload": 0, "merged": 0, "merged_segments": 0}
    last_l4 = l4_default
    for p in rec["x_packets"]:
        stats["entries"] += 1
        b = int(p["bytes"])
        sign = 1 if b > 0 else -1
        ts = parse_ts_us(p["timestamp_start"])
        k = int(p.get("packets", 1))
        if k == 1:
            ip_hdr = int(p.get("ip_header_len", IP_HEADER))
            l4 = int(p["tcp_header_len"]) if tcp and "tcp_header_len" in p else l4_default
            last_l4 = l4 if tcp else last_l4
            flags = int(p["tcp_flags"], 2) if tcp and "tcp_flags" in p else 0
            sizes = [abs(b)]
        else:
            stats["multi"] += 1
            ip_hdr, l4, flags = IP_HEADER, (last_l4 if tcp else UDP_HEADER), (ACK if tcp else 0)
            q, r = divmod(abs(b), k)
            sizes = [q + (i < r) for i in range(k)]
        for size in sizes:
            payload = size - ip_hdr - l4
            if payload < 0:
                stats["neg_payload"] += 1
                payload = 0
            rows.append((ts, payload, sign, l4, flags, size))
    if tcp and split_offload:
        return Packets.of(split_merged(rows, stats)), stats
    return Packets.of([r[:5] for r in rows]), stats


def connection_key(rec: dict) -> tuple[tuple[str, int, int], int]:
    """Klucz połączenia (protokół, mniejszy port, większy port) i mnożnik znaku do tego układu.

    Bez adresów IP połączenie identyfikują tylko protokół i porty; rekordy pmacct z tym samym
    kluczem łączymy w jeden strumień, bo pmacct tnie długie połączenia na kilka rekordów.
    """
    a, b = int(rec.get("port_src", 0)), int(rec.get("port_dst", 0))
    return (rec["ip_proto"], min(a, b), max(a, b)), (1 if a <= b else -1)


@dataclass
class FileResult:
    flows: pd.DataFrame
    removed: Counter  # powód → liczba rekordów
    removed_packets: Counter
    stats: Counter


def build_file(member: str, service: str, zip_path: Path | None = None,
               split_offload: bool = True) -> FileResult:
    """Przepływy CICFlowMeter z jednego pliku JSON (wszystkie rekordy, bez próbkowania)."""
    conns: dict[tuple[str, int, int], list[Packets]] = defaultdict(list)
    removed, removed_pk, stats = Counter(), Counter(), Counter()
    for rec in iter_records(member, zip_path):
        stats["records"] += 1
        reason = filter_reason(rec["ip_proto"], int(rec.get("port_src", 0)),
                               int(rec.get("port_dst", 0)))
        if reason:
            removed[reason] += 1
            removed_pk[reason] += len(rec["x_packets"])
            continue
        pk, st = record_packets(rec, split_offload)
        stats.update(st)
        key, mult = connection_key(rec)
        conns[key].append(Packets(pk.ts, pk.payload, pk.sign * mult, pk.header, pk.flags))
    rows = []
    for (proto, port_a, port_b), parts in conns.items():
        pk = Packets(*(np.concatenate([getattr(p, f) for p in parts])
                       for f in ("ts", "payload", "sign", "header", "flags")))
        pk = pk[np.argsort(pk.ts, kind="stable")]
        stats["connections"] += 1
        stats["records_merged"] += len(parts) - 1
        for start, end, fsign in split_flows(pk, tcp=proto == "tcp"):
            f = flow_features(pk[start:end], fsign, PROTOCOLS[proto])
            src, dst = (port_a, port_b) if fsign == 1 else (port_b, port_a)
            rows.append({"service": service, "source_file": member,
                         "ts": pd.Timestamp(int(pk.ts[start]), unit="us"),
                         "Src Port": src, "Dst Port": dst, **f})
    stats["flows_raw"] = len(rows)
    return FileResult(pd.DataFrame(rows), removed, removed_pk, stats)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Jak preprocess.drop_invalid_and_duplicates: usuwa inf/NaN i duplikaty (cechy + usługa)."""
    feats = [c for c in df.columns if c in FEATURES]
    bad = ~np.isfinite(df[feats].to_numpy(dtype=float)).all(axis=1)
    valid = df[~bad]
    dup = valid.duplicated(subset=feats + ["service"])
    return valid[~dup].reset_index(drop=True), {"invalid": int(bad.sum()),
                                                 "duplicates": int(dup.sum())}


def build(zip_path: Path | None = None,
          split_offload: bool = True) -> tuple[pd.DataFrame, str]:
    """Wszystkie trzy usługi bez VPN → (przepływy, raport markdown)."""
    parts, log = [], ["# USBVPN2022 → przepływy CICFlowMeter (E7)\n",
                      "Źródło: Naas, Fesl, „Encrypted VPN Dataset” (USBVPN2022), Zenodo "
                      "10.5281/zenodo.7301756, licencja CC BY 4.0. Tylko pliki `Non VPN`.\n",
                      "Scalone segmenty TCP: "
                      f"{'rozbite na segmenty MSS' if split_offload else 'bez zmian'}.\n"]
    for name, service in SERVICES.items():
        member = f"{ARCHIVE_ROOT}/Non VPN/{name}.json"
        res = build_file(member, service, zip_path, split_offload)
        flows, cl = clean(res.flows)
        parts.append(flows)
        s = res.stats
        log += [f"## {name}.json → {service}\n",
                f"- rekordy pmacct: {s['records']:,}; usunięte filtrem: "
                f"{sum(res.removed.values()):,}; połączenia (protokół + porty): "
                f"{s['connections']:,} (scalono {s['records_merged']:,} rekordów)",
                f"- wpisy x_packets: {s['entries']:,}, w tym z packets > 1: {s['multi']:,}; "
                f"pakiety z ujemnym ładunkiem (ustawione na 0): {s['neg_payload']:,}; "
                f"scalone segmenty TCP: {s['merged']:,} (→ {s['merged_segments']:,} pakietów)",
                f"- przepływy CICFlowMeter: {s['flows_raw']:,}; inf/NaN: {cl['invalid']:,}; "
                f"duplikaty: {cl['duplicates']:,}; **zostaje {len(flows):,}**\n",
                "| powód usunięcia | rekordy | wpisy x_packets |", "| --- | ---: | ---: |",
                *[f"| {k} | {v:,} | {res.removed_packets[k]:,} |"
                  for k, v in res.removed.most_common()], ""]
    df = pd.concat(parts, ignore_index=True)
    df = df.astype({c: "float64" for c in FEATURES})
    return df[META_COLS + FEATURES], "\n".join(log)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download")
    b = sub.add_parser("build", help="przepływy z plików Non VPN → data/external/")
    b.add_argument("--out", type=Path, default=EXTERNAL / "usbvpn_flows.parquet")
    b.add_argument("--report", type=Path,
                   default=ROOT / "reports" / "results" / "06_e7" / "usbvpn_przeplywy.md")
    b.add_argument("--no-split-offload", action="store_true",
                   help="zostaw scalone segmenty TCP (wariant do porównania)")
    args = p.parse_args(argv)
    if args.cmd == "download":
        print(f"OK: {download()} (MD5 zgodne)")
    elif args.cmd == "build":
        df, report = build(download(), split_offload=not args.no_split_offload)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(args.out, index=False)
        args.report.write_text(report, encoding="utf-8")
        print(report)
        print(f"\nZapisano {len(df):,} przepływów -> {args.out}")


if __name__ == "__main__":
    main()
