"""E6: wczesna klasyfikacja VoIP vs Video na PCAP-ach ISCX VPN-nonVPN 2016 (etap 07).

  przeplywy  PCAP-y → przepływy CICFlowMeter (`pcap_flows`) → data/external/iscx_e6/
  dopasuj    etykiety z Darknet.CSV przez 5-krotkę i czas, filtr tła i czyszczenie jak
             w preprocess.py, raport dopasowania i zgodności cech z Darknet.CSV
  prefiksy   cechy z pierwszych N pakietów przepływów z e6_flows.parquet (sesja 2);
             przepływ krótszy niż N daje cechy z wszystkich pakietów (decyzja autora)
Ocena modeli: e6_ocena.py.

Etykieta pochodzi z Darknet.CSV, nie z nazwy pliku (docs/decyzje.md, wpis 2026-11-19).
Czas w Darknet.CSV to czas lokalny miejsca nagrania (ADT, UTC-3) z dokładnością do sekundy;
przesunięcie zmierzone na próbie 10 plików: różnica −3 h co do sekundy.
"""
import argparse
import re
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np
import pandas as pd

from pcap_flows import FlowPackets, file_flow_packets, file_flows
from preprocess import RAW, background_reason, drop_invalid_and_duplicates, load_raw
from usbvpn import FEATURES

ROOT = Path(__file__).resolve().parents[1]
PCAP_DIR = ROOT / "data" / "external" / "iscx_vpn2016"
E6_DIR = ROOT / "data" / "external" / "iscx_e6"
RESULTS = ROOT / "reports" / "results" / "07_e6"

# Pliki z rozmowami i wideo; etykietę i tak bierzemy z Darknet. Audio zostaje, bo pokazuje,
# jak Darknet oznaczył rozmowy głosowe (Audio-Streaming, a nie VoIP).
FILE_PATTERN = re.compile(r"voipbuster|video|netflix|youtube|vimeo|audio", re.IGNORECASE)
TRAFFIC_TYPES = ["NonVPN", "VPN"]
SERVICES = ["VoIP", "Video"]
DARKNET_UTC_OFFSET = pd.Timedelta(hours=-3)
MATCH_TOLERANCE = pd.Timedelta(seconds=1)
KEY = ["Src IP", "Src Port", "Dst IP", "Dst Port", "Protocol"]
COUNTS = ["Total Fwd Packet", "Total Bwd packets"]
# Zgodność cech: równe co do zaokrąglenia albo w granicy 1% (czasy w µs z zaokrąglenia znacznika)
REL_CLOSE = 0.01
FIRST_N = (5, 10, 20, 50)
FULL_FLOW = 0  # wartość n_first dla cech z całego przepływu
FLOW_ID = ["source_file", "Src IP", "Src Port", "Dst IP", "Dst Port", "ts_us"]
LABELS = ["traffic_type", "service"]


def select_files(pcap_dir: Path) -> list[Path]:
    files = sorted(p for p in pcap_dir.glob("*/*.pcap*") if FILE_PATTERN.search(p.name))
    if not files:
        raise FileNotFoundError(f"{pcap_dir}: brak plików PCAP pasujących do {FILE_PATTERN.pattern}")
    return files


def build_flows(files: list[Path], pcap_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Przepływy ze wszystkich plików i tabela liczników na plik."""
    frames, stats = [], []
    for path in files:
        rel = path.relative_to(pcap_dir).as_posix()
        df, st = file_flows(path, rel)
        frames.append(df)
        stats.append({"source_file": rel, **st})
        print(f"{rel}: {st['packets']:,} pakietów, {st['flows']:,} przepływów", flush=True)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(stats).fillna(0)


def darknet_rows(raw: pd.DataFrame) -> pd.DataFrame:
    """Wiersze kampanii VPN-nonVPN z czasem startu przepływu jako Timestamp."""
    d = raw[raw["traffic_type"].isin(TRAFFIC_TYPES)]
    return d.assign(dts=pd.to_datetime(d["Timestamp"], format="%d/%m/%Y %I:%M:%S %p"),
                    darknet_row=d.index, label=d["traffic_type"] + "|" + d["service_raw"].str.lower())


def candidates(flows: pd.DataFrame, darknet: pd.DataFrame,
               offset: pd.Timedelta, tol: pd.Timedelta) -> pd.DataFrame:
    """Pary (przepływ z PCAP, wiersz Darknet) o tej samej 5-krotce i czasie startu w granicy tol."""
    local = (pd.to_datetime(flows["ts_us"], unit="us") + offset).dt.floor("s")
    f = flows[KEY + COUNTS].assign(fid=flows.index, local_s=local,
                                   Protocol=flows["Protocol"].astype(int))
    d = darknet[KEY + COUNTS + ["dts", "darknet_row", "label", "traffic_type", "service",
                                "service_raw"]]
    m = f.merge(d, on=KEY, suffixes=("", "_dk"))
    dt = (m["dts"] - m["local_s"]).abs()
    m = m.assign(dt_s=dt.dt.total_seconds(),
                 same_counts=(m[COUNTS[0]] == m[COUNTS[0] + "_dk"])
                 & (m[COUNTS[1]] == m[COUNTS[1] + "_dk"]))
    return m[dt <= tol]


def resolve(flows: pd.DataFrame, cand: pd.DataFrame) -> pd.DataFrame:
    """Status dopasowania każdego przepływu: dopasowany / brak / niejednoznaczny / duplikat.

    Przy kilku kandydatach z tą samą etykietą bierzemy ten o tych samych licznikach pakietów,
    potem najbliższy w czasie. Różne etykiety → niejednoznaczny (odrzucony). Jeden wiersz
    Darknet dopasowany do kilku przepływów (np. to samo połączenie w dwóch plikach) zostaje
    przy jednym przepływie, pozostałe dostają status duplikat.
    """
    n_labels = cand.groupby("fid")["label"].nunique()
    best = (cand.sort_values(["fid", "same_counts", "dt_s"], ascending=[True, False, True])
            .drop_duplicates("fid").set_index("fid"))
    status = pd.Series("brak", index=flows.index)
    status[n_labels.index] = np.where(n_labels > 1, "niejednoznaczny", "dopasowany")
    ok = best[status[best.index].eq("dopasowany").to_numpy()]
    keep = (ok.sort_values(["darknet_row", "same_counts", "dt_s"], ascending=[True, False, True])
            .drop_duplicates("darknet_row"))
    status[ok.index.difference(keep.index)] = "duplikat"
    cols = ["traffic_type", "service", "service_raw", "darknet_row", "same_counts", "dt_s"]
    return flows.assign(match=status).join(keep[cols])


def file_table(matched: pd.DataFrame) -> pd.DataFrame:
    """Na plik: liczba przepływów według statusu i etykiety Darknet."""
    status = pd.crosstab(matched["source_file"], matched["match"])
    ok = matched[matched["match"] == "dopasowany"]
    labels = pd.crosstab(ok["source_file"], ok["traffic_type"] + "|" + ok["service_raw"].str.lower())
    return status.join(labels, how="left").fillna(0).astype(int)


def coverage_table(matched: pd.DataFrame, darknet: pd.DataFrame) -> pd.DataFrame:
    """Ile wierszy Darknet z VoIP i Video ma swój przepływ w PCAP-ach (przed filtrem tła)."""
    d = darknet[darknet["service"].isin(SERVICES)]
    found = set(matched.loc[matched["match"] == "dopasowany", "darknet_row"].astype(int))
    t = d.assign(found=d["darknet_row"].isin(found)).groupby(["traffic_type", "service"])
    out = t.agg(darknet=("found", "size"), dopasowane=("found", "sum"))
    return out.assign(pokrycie=(out["dopasowane"] / out["darknet"]).round(3))


def clean_e6(matched: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """VoIP i Video z dopasowaniem, bez ruchu tła, bez inf/NaN i duplikatów (jak preprocess.py)."""
    df = matched[(matched["match"] == "dopasowany") & matched["service"].isin(SERVICES)]
    reason = background_reason(df)
    kept = df[reason == ""]
    clean, st = drop_invalid_and_duplicates(kept, FEATURES)
    return clean, {"voip_video": len(df), "background": int((reason != "").sum()), **st,
                   "final": len(clean)}


def feature_agreement(clean: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Na cechę: udział przepływów równych wierszowi Darknet (co do zaokrąglenia) i w granicy 1%."""
    ours = clean[FEATURES].to_numpy(dtype=float)
    theirs = raw.loc[clean["darknet_row"].astype(int), FEATURES].apply(
        pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    equal = np.isclose(ours, theirs, rtol=1e-6, atol=1e-6)
    close = np.isclose(ours, theirs, rtol=REL_CLOSE, atol=1.0)
    out = pd.DataFrame({"rowne": equal.mean(axis=0), "w_1proc": close.mean(axis=0)}, index=FEATURES)
    out.index.name = "cecha"
    all_row = pd.DataFrame({"rowne": [equal.all(axis=1).mean()], "w_1proc": [close.all(axis=1).mean()]},
                           index=["(wszystkie 55 naraz)"])
    return pd.concat([all_row, out.sort_values("rowne")]).round(4)


def report(stats: pd.DataFrame, matched: pd.DataFrame, cand: pd.DataFrame, cov: pd.DataFrame,
           clean: pd.DataFrame, clean_stats: dict[str, int], agree: pd.DataFrame) -> str:
    skipped = stats.drop(columns=["source_file"]).sum().astype(int)
    status = matched["match"].value_counts()
    final = clean.groupby(["traffic_type", "service"]).size().rename("przepływy").to_frame()
    return "\n".join([
        "# E6, sesja 1: przepływy z PCAP-ów ISCX VPN-nonVPN i etykiety z Darknet.CSV", "",
        f"Plików: {len(stats)}. Ramki i pominięcia (suma): " + ", ".join(
            f"{k} {v:,}" for k, v in skipped.items()) + ".", "",
        f"Dopasowanie: 5-krotka i czas startu (Darknet = UTC {DARKNET_UTC_OFFSET / pd.Timedelta(hours=1):+.0f} h,"
        f" tolerancja {MATCH_TOLERANCE.total_seconds():.0f} s).", "",
        "## Status przepływów (wszystkie pliki)", "", status.to_frame("przepływy").to_markdown(), "",
        f"Kandydaci z tymi samymi licznikami pakietów: {cand['same_counts'].mean():.1%} par.", "",
        "## Pokrycie wierszy Darknet (VoIP, Video; przed filtrem tła)", "", cov.to_markdown(), "",
        "## Po filtrze tła i czyszczeniu (jak preprocess.py)", "",
        ", ".join(f"{k}: {v:,}" for k, v in clean_stats.items()), "", final.to_markdown(), "",
        "## Zgodność cech pełnego przepływu z Darknet.CSV (po czyszczeniu)", "",
        "`rowne`: równe co do zaokrąglenia; `w_1proc`: różnica ≤ 1% albo ≤ 1 jednostki.", "",
        agree.head(15).to_markdown(), "",
        "Pełna tabela: `zgodnosc_cech.csv`; na plik: `dopasowanie_pliki.csv`.", ""])


def iter_file_flows(pcap_dir: Path, files: list[str]) -> Iterator[tuple[str, FlowPackets]]:
    for rel in files:
        stats: Counter = Counter()
        yield from ((rel, f) for f in file_flow_packets(pcap_dir / rel, stats))
        print(f"{rel}: {stats['packets']:,} pakietów", flush=True)


def prefix_features(flows: Iterable[tuple[str, FlowPackets]], wanted: pd.DataFrame,
                    first_n: tuple[int, ...] = FIRST_N) -> pd.DataFrame:
    """Cechy z pierwszych N pakietów i z całego przepływu (n_first = FULL_FLOW) dla przepływów
    z `wanted` (klucz FLOW_ID), z ich etykietami; brak przepływu albo duplikat klucza to błąd."""
    if wanted.duplicated(FLOW_ID).any():
        raise ValueError("e6_flows: powtórzony klucz przepływu " + ", ".join(FLOW_ID))
    keys = set(wanted[FLOW_ID].itertuples(index=False, name=None))
    rows = [{"source_file": rel, **f.meta, "n_first": n,
             **f.features(None if n == FULL_FLOW else n)}
            for rel, f in flows if (rel, *(f.meta[c] for c in FLOW_ID[1:])) in keys
            for n in (FULL_FLOW, *first_n)]
    found = pd.DataFrame(rows, columns=FLOW_ID + ["n_packets", "n_first", *FEATURES])
    if found.duplicated(FLOW_ID + ["n_first"]).any():
        raise ValueError("PCAP-y dają dwa przepływy o tym samym kluczu " + ", ".join(FLOW_ID))
    missing = len(wanted) - found[FLOW_ID].drop_duplicates().shape[0]
    if missing:
        raise ValueError(f"{missing} przepływów z e6_flows nie ma w PCAP-ach (inne pliki lub kod?)")
    return found.merge(wanted[FLOW_ID + LABELS], on=FLOW_ID, validate="many_to_one")


def full_flow_mismatches(prefixes: pd.DataFrame, wanted: pd.DataFrame) -> int:
    """Liczba przepływów, w których cechy pełnego przepływu różnią się od e6_flows."""
    full = prefixes[prefixes["n_first"] == FULL_FLOW].merge(
        wanted[FLOW_ID + FEATURES], on=FLOW_ID, suffixes=("", "_e6"))
    ours = full[FEATURES].to_numpy(dtype=float)
    theirs = full[[f + "_e6" for f in FEATURES]].to_numpy(dtype=float)
    return int((~np.isclose(ours, theirs, rtol=1e-9, atol=0, equal_nan=True)).any(axis=1).sum())


def prefix_report(prefixes: pd.DataFrame, mismatches: int) -> str:
    """Na N: udział przepływów obciętych (dłuższych niż N) i z wartością nieskończoną lub NaN."""
    rows = []
    for (n, svc), g in prefixes[prefixes["n_first"] != FULL_FLOW].groupby(["n_first", "service"]):
        rows.append({"N": n, "usługa": svc, "przepływy": len(g),
                     "obcięte": round(float((g["n_packets"] > n).mean()), 3),
                     "inf/NaN": int((~np.isfinite(g[FEATURES].to_numpy(dtype=float))).any(axis=1).sum())})
    return "\n".join([
        "# E6, sesja 2: cechy z pierwszych N pakietów", "",
        f"Przepływów: {prefixes[FLOW_ID].drop_duplicates().shape[0]:,}. Przepływ krótszy niż N"
        " daje cechy ze wszystkich swoich pakietów, czyli takie jak pełny przepływ.", "",
        f"Cechy pełnego przepływu różne od e6_flows.parquet: {mismatches} przepływów.", "",
        "`obcięte`: udział przepływów dłuższych niż N (tylko w nich cechy różnią się od pełnych).",
        "", pd.DataFrame(rows).to_markdown(index=False), ""])


def cmd_przeplywy(args: argparse.Namespace) -> None:
    files = select_files(args.pcap_dir)
    flows, stats = build_flows(files, args.pcap_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    flows.to_parquet(args.out_dir / "przeplywy.parquet", index=False)
    stats.to_csv(args.out_dir / "przeplywy_pliki.csv", index=False)
    print(f"Zapisano {len(flows):,} przepływów z {len(files)} plików -> {args.out_dir}")


def cmd_dopasuj(args: argparse.Namespace) -> None:
    flows = pd.read_parquet(args.out_dir / "przeplywy.parquet")
    stats = pd.read_csv(args.out_dir / "przeplywy_pliki.csv")
    raw = load_raw(args.raw)
    darknet = darknet_rows(raw)
    cand = candidates(flows, darknet, DARKNET_UTC_OFFSET, MATCH_TOLERANCE)
    matched = resolve(flows, cand)
    cov = coverage_table(matched, darknet)
    clean, clean_stats = clean_e6(matched)
    agree = feature_agreement(clean, raw)
    clean.to_parquet(args.out_dir / "e6_flows.parquet", index=False)
    args.results.mkdir(parents=True, exist_ok=True)
    file_table(matched).to_csv(args.results / "dopasowanie_pliki.csv")
    agree.to_csv(args.results / "zgodnosc_cech.csv")
    text = report(stats, matched, cand, cov, clean, clean_stats, agree)
    (args.results / "dopasowanie.md").write_text(text, encoding="utf-8")
    print(text)


def cmd_prefiksy(args: argparse.Namespace) -> None:
    wanted = pd.read_parquet(args.out_dir / "e6_flows.parquet")
    files = sorted(wanted["source_file"].unique())
    prefixes = prefix_features(iter_file_flows(args.pcap_dir, files), wanted)
    mismatches = full_flow_mismatches(prefixes, wanted)
    if mismatches:
        raise ValueError(f"{mismatches} przepływów ma inne cechy pełnego przepływu niż e6_flows; "
                         "przelicz `przeplywy` i `dopasuj` tym samym kodem")
    prefixes.to_parquet(args.out_dir / "e6_prefiksy.parquet", index=False)
    text = prefix_report(prefixes, mismatches)
    args.results.mkdir(parents=True, exist_ok=True)
    (args.results / "prefiksy.md").write_text(text, encoding="utf-8")
    print(text)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out-dir", type=Path, default=E6_DIR)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("przeplywy", help="PCAP-y → przeplywy.parquet")
    a.add_argument("--pcap-dir", type=Path, default=PCAP_DIR)
    b = sub.add_parser("dopasuj", help="etykiety z Darknet.CSV, czyszczenie, raport")
    b.add_argument("--raw", type=Path, default=RAW)
    b.add_argument("--results", type=Path, default=RESULTS)
    c = sub.add_parser("prefiksy", help="cechy z pierwszych N pakietów → e6_prefiksy.parquet")
    c.add_argument("--pcap-dir", type=Path, default=PCAP_DIR)
    c.add_argument("--results", type=Path, default=RESULTS)
    args = p.parse_args(argv)
    {"przeplywy": cmd_przeplywy, "dopasuj": cmd_dopasuj, "prefiksy": cmd_prefiksy}[args.cmd](args)


if __name__ == "__main__":
    main()
