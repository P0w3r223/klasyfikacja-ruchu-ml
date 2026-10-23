"""Przygotowanie podzbioru CIC-Darknet2020 do eksperymentów (wariant A).

Kroki: ujednolicenie etykiet -> wybór podzbioru -> odfiltrowanie ruchu tła
-> czyszczenie (inf/NaN, duplikaty) -> definicja sesji -> zapis parquet.
Każdy krok wypisuje liczby przepływów; raport trafia też do reports/preprocess_report.md.

Użycie: python src/preprocess.py [--gap-min 5] [--raw PLIK] [--out-dir KATALOG] [--reports-dir KATALOG]
"""
import argparse
import ipaddress
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "Darknet.CSV"
KNOWN_BAD_LINES = 1  # wiersz 328 w Darknet.CSV z data-raw-v1
OUT_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"

SERVICE_MAP = {
    "browsing": "WWW",
    "voip": "VoIP",
    "video-streaming": "Video",
    "audio-streaming": "Audio",  # tylko test kontrolny E5
}
TRAFFIC_TYPES = ["Non-Tor", "NonVPN", "VPN"]
CAMPAIGN = {"Non-Tor": "tor-nontor", "NonVPN": "vpn-nonvpn", "VPN": "vpn-nonvpn"}
TUNNEL = {"Non-Tor": "plain", "NonVPN": "plain", "VPN": "vpn"}

# Cechy-skróty: identyfikują sesję/host, a nie zachowanie ruchu. Służą tylko do definicji sesji.
ID_COLS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp"]
META_COLS = ["traffic_type", "service", "campaign", "tunnel", "session", "ts",
             "Src IP", "Dst IP", "Src Port", "Dst Port"]

# Ruch tła systemu operacyjnego, który trafił do plików z etykietą usługi.
BACKGROUND_PORTS = {
    53: "DNS", 5353: "mDNS", 5355: "LLMNR", 137: "NetBIOS", 138: "NetBIOS",
    139: "NetBIOS", 1900: "SSDP", 67: "DHCP", 68: "DHCP", 123: "NTP",
    161: "SNMP", 162: "SNMP",
    17500: "Dropbox LAN sync",
}


def is_multicast_or_broadcast(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    # Końcówka .255 to przybliżenie broadcastu podsieci (maska nieznana). Odcina też 3 przepływy
    # TCP Video do zwykłych hostów; zostawione świadomie, patrz decyzje.md (etap 02).
    return addr.is_multicast or ip == "255.255.255.255" or ip.endswith(".255")


def _count_data_lines(path: Path) -> int:
    """Niepuste wiersze pliku bez nagłówka (puste pandas pomija i nie są uszkodzone)."""
    with path.open("rb") as f:
        return sum(1 for line in f if line.strip()) - 1


def load_raw(path: Path) -> pd.DataFrame:
    # Wiersz 328 jest uszkodzony (ok. 8 MB bajtów zerowych) - pomijamy go. Każdy inny
    # pominięty wiersz oznacza inny plik niż data-raw-v1, więc przerywamy.
    df = pd.read_csv(path, low_memory=False, on_bad_lines="skip")
    skipped = _count_data_lines(path) - len(df)
    if skipped != KNOWN_BAD_LINES:
        raise ValueError(f"{path}: pominięto {skipped} uszkodzonych wierszy, oczekiwano "
                         f"{KNOWN_BAD_LINES} (wiersz 328); sprawdź, czy to plik z data-raw-v1")
    df = df.rename(columns={"Label": "traffic_type", "Label.1": "service_raw"})
    df["service"] = df["service_raw"].str.lower().map(SERVICE_MAP)
    return df


def background_reason(df: pd.DataFrame) -> pd.Series:
    reason = pd.Series("", index=df.index)
    reason[~df["Protocol"].isin([6, 17])] = "protokół inny niż TCP/UDP"
    for col in ["Dst Port", "Src Port"]:
        hit = df[col].map(BACKGROUND_PORTS)
        reason = reason.mask((reason == "") & hit.notna(), hit)
    mb = df["Dst IP"].map(is_multicast_or_broadcast)
    reason[(reason == "") & mb] = "multicast/broadcast"
    return reason


def ip_pair(df: pd.DataFrame) -> pd.Series:
    """Nieuporządkowana para IP jako tekst „mniejszy|większy”."""
    a = df["Src IP"].where(df["Src IP"] < df["Dst IP"], df["Dst IP"])
    b = df["Src IP"].where(df["Src IP"] >= df["Dst IP"], df["Dst IP"])
    return a + "|" + b


def assign_sessions(df: pd.DataFrame, gap_min: float) -> pd.Series:
    """Sesja = ta sama nieuporządkowana para IP, ta sama etykieta, przerwa <= gap_min."""
    key = df["traffic_type"] + "|" + df["service"] + "|" + ip_pair(df)
    order = pd.DataFrame({"key": key, "ts": df["ts"]}).sort_values(["key", "ts"])
    new = order["key"].ne(order["key"].shift()) | (
        order["ts"].diff() > pd.Timedelta(minutes=gap_min)
    )
    return new.cumsum().reindex(df.index).astype(int)


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in ID_COLS + ["traffic_type", "service_raw", "service"]]


def drop_invalid_and_duplicates(
    df: pd.DataFrame, feat_cols: list[str]
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Usuwa wiersze z inf/NaN i duplikaty (te same cechy i etykiety).

    Zwraca oczyszczoną ramkę i liczności: invalid, duplicates, conflicts
    (przepływy o identycznych cechach, ale różnych etykietach - zostają).
    """
    num = df[feat_cols].apply(pd.to_numeric, errors="coerce")
    bad = ~np.isfinite(num).all(axis=1)
    valid = df[~bad]
    dup = valid.duplicated(subset=feat_cols + ["traffic_type", "service"])
    clean = valid[~dup].copy()
    conflict = clean.duplicated(subset=feat_cols, keep=False)
    stats = {"invalid": int(bad.sum()), "duplicates": int(dup.sum()),
             "conflicts": int(conflict.sum())}
    return clean, stats


def constant_features(df: pd.DataFrame, feat_cols: list[str]) -> list[str]:
    """Cechy stałe w ruchu głównym; Audio (tylko E5) nie decyduje o liście cech."""
    main_mask = df["service"] != "Audio"
    return [c for c in feat_cols if df.loc[main_mask, c].nunique() <= 1]


def add_session_columns(df: pd.DataFrame, gap_min: float) -> pd.DataFrame:
    df = df.assign(ts=pd.to_datetime(df["Timestamp"], format="%d/%m/%Y %I:%M:%S %p"))
    return df.assign(
        session=assign_sessions(df, gap_min),
        campaign=df["traffic_type"].map(CAMPAIGN),
        tunnel=df["traffic_type"].map(TUNNEL),
    )


def session_summary(df: pd.DataFrame) -> pd.DataFrame:
    s = df.groupby(["traffic_type", "service"]).agg(
        flows=("session", "size"), sessions=("session", "nunique"))
    largest = df.groupby(["traffic_type", "service", "session"]).size().groupby(level=[0, 1]).max()
    return s.assign(largest_session_share=(largest / s["flows"]).round(2))


def step_section(name: str, df: pd.DataFrame) -> str:
    tab = pd.crosstab(df["service"], df["traffic_type"], margins=True)
    return f"### {name}: {len(df):,} przepływów\n\n{tab.to_markdown()}\n"


def filter_background(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Zwraca ramkę bez ruchu tła i sekcję raportu z liczbą usuniętych przepływów."""
    reason = background_reason(df)
    removed = reason[reason != ""]
    tab = pd.crosstab(removed, df.loc[removed.index, "service"])
    return df[reason == ""].copy(), f"### Odfiltrowany ruch tła\n\n{tab.to_markdown()}\n"


@dataclass(frozen=True)
class PreprocessResult:
    flows: pd.DataFrame
    features_json: str
    report: str


def build(raw: pd.DataFrame, gap_min: float) -> PreprocessResult:
    """Cały potok bez wejścia/wyjścia: ramka z load_raw -> przepływy, lista cech, raport."""
    log = [f"Surowy plik: {len(raw):,} przepływów (po pominięciu uszkodzonego wiersza 328)\n"]

    df = raw[raw["traffic_type"].isin(TRAFFIC_TYPES) & raw["service"].notna()].copy()
    log.append(step_section("1. Podzbiór (bez Tor, 3 usługi + Audio do E5)", df))

    df, background_section = filter_background(df)
    log += [background_section, step_section("2. Po odfiltrowaniu ruchu tła", df)]

    feat_cols = feature_columns(df)
    df, stats = drop_invalid_and_duplicates(df, feat_cols)
    log += [
        f"Usunięte wiersze z inf/NaN: {stats['invalid']:,}\n",
        f"Usunięte duplikaty (te same cechy i etykiety): {stats['duplicates']:,}\n",
        f"Przepływy o identycznych cechach, ale różnych etykietach: {stats['conflicts']:,}"
        " (zostają; ograniczają osiągalną dokładność)\n",
        step_section("3. Po czyszczeniu", df),
    ]

    const = constant_features(df, feat_cols)
    features = [c for c in feat_cols if c not in const]
    log += [f"Cechy stałe usunięte ({len(const)}): {', '.join(const)}\n",
            f"Cechy do modelowania: {len(features)}\n"]

    df = add_session_columns(df, gap_min)
    log.append(f"### Sesje (przerwa > {gap_min:g} min = nowa sesja)\n\n"
               f"{session_summary(df).to_markdown()}\n")

    out = df[META_COLS + features].reset_index(drop=True)
    out = out.astype({c: "float64" for c in features})
    features_json = json.dumps(
        {"features": features, "dropped_constant": const, "session_gap_min": gap_min},
        indent=2, ensure_ascii=False)
    return PreprocessResult(out, features_json,
                            "# Raport z przygotowania danych\n\n" + "\n".join(log))


def write_outputs(result: PreprocessResult, out_dir: Path, reports_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    result.flows.to_parquet(out_dir / "flows.parquet", index=False)
    (out_dir / "features.json").write_text(result.features_json, encoding="utf-8")
    # Kopia listy cech w repozytorium - mała, potrzebna aplikacji i do odtwarzalności.
    (reports_dir / "features.json").write_text(result.features_json, encoding="utf-8")
    (reports_dir / "preprocess_report.md").write_text(result.report, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--gap-min", type=float, default=5.0)
    p.add_argument("--raw", type=Path, default=RAW, help="surowy Darknet.CSV")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR,
                   help="katalog na flows.parquet i features.json")
    p.add_argument("--reports-dir", type=Path, default=REPORTS_DIR,
                   help="katalog na preprocess_report.md i kopię features.json")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    result = build(load_raw(args.raw), args.gap_min)
    print(result.report)
    write_outputs(result, args.out_dir, args.reports_dir)
    print(f"\nZapisano {len(result.flows):,} przepływów -> {args.out_dir / 'flows.parquet'}")


if __name__ == "__main__":
    main()
