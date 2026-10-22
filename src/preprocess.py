"""Przygotowanie podzbioru CIC-Darknet2020 do eksperymentów (wariant A).

Kroki: ujednolicenie etykiet -> wybór podzbioru -> odfiltrowanie ruchu tła
-> czyszczenie (inf/NaN, duplikaty) -> definicja sesji -> zapis parquet.
Każdy krok wypisuje liczby przepływów; raport trafia też do reports/preprocess_report.md.

Użycie: python src/preprocess.py [--gap-min 5] [--raw PLIK] [--out-dir KATALOG] [--reports-dir KATALOG]
"""
import argparse
import ipaddress
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "Darknet.CSV"
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


def load_raw(path: Path) -> pd.DataFrame:
    # Wiersz 328 jest uszkodzony (ok. 8 MB bajtów zerowych) - pomijamy go.
    df = pd.read_csv(path, low_memory=False, on_bad_lines="skip")
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


def assign_sessions(df: pd.DataFrame, gap_min: float) -> pd.Series:
    """Sesja = ta sama nieuporządkowana para IP, ta sama etykieta, przerwa <= gap_min."""
    a = df["Src IP"].where(df["Src IP"] < df["Dst IP"], df["Dst IP"])
    b = df["Src IP"].where(df["Src IP"] >= df["Dst IP"], df["Dst IP"])
    key = df["traffic_type"] + "|" + df["service"] + "|" + a + "|" + b
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--gap-min", type=float, default=5.0)
    p.add_argument("--raw", type=Path, default=RAW, help="surowy Darknet.CSV")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR,
                   help="katalog na flows.parquet i features.json")
    p.add_argument("--reports-dir", type=Path, default=REPORTS_DIR,
                   help="katalog na preprocess_report.md i kopię features.json")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()

    log: list[str] = []

    def step(name: str, d: pd.DataFrame) -> None:
        tab = pd.crosstab(d["service"], d["traffic_type"], margins=True)
        log.append(f"### {name}: {len(d):,} przepływów\n\n{tab.to_markdown()}\n")
        print(f"\n== {name}: {len(d):,}\n{tab}")

    df = load_raw(args.raw)
    log.append(f"Surowy plik: {len(df):,} przepływów (po pominięciu uszkodzonego wiersza 328)\n")

    df = df[df["traffic_type"].isin(TRAFFIC_TYPES) & df["service"].notna()].copy()
    step("1. Podzbiór (bez Tor, 3 usługi + Audio do E5)", df)

    reason = background_reason(df)
    removed = reason[reason != ""]
    tab = pd.crosstab(removed, df.loc[removed.index, "service"])
    log.append(f"### Odfiltrowany ruch tła\n\n{tab.to_markdown()}\n")
    print(f"\n== Ruch tła (usunięty)\n{tab}")
    df = df[reason == ""].copy()
    step("2. Po odfiltrowaniu ruchu tła", df)

    feat_cols = feature_columns(df)
    df, stats = drop_invalid_and_duplicates(df, feat_cols)
    log.append(f"Usunięte wiersze z inf/NaN: {stats['invalid']:,}\n")
    log.append(f"Usunięte duplikaty (te same cechy i etykiety): {stats['duplicates']:,}\n")
    log.append(f"Przepływy o identycznych cechach, ale różnych etykietach: {stats['conflicts']:,}"
               " (zostają; ograniczają osiągalną dokładność)\n")
    step("3. Po czyszczeniu", df)

    main_mask = df["service"] != "Audio"
    const = [c for c in feat_cols if df.loc[main_mask, c].nunique() <= 1]
    features = [c for c in feat_cols if c not in const]
    log.append(f"Cechy stałe usunięte ({len(const)}): {', '.join(const)}\n")
    log.append(f"Cechy do modelowania: {len(features)}\n")

    df["ts"] = pd.to_datetime(df["Timestamp"], format="%d/%m/%Y %I:%M:%S %p")
    df["session"] = assign_sessions(df, args.gap_min)
    df["campaign"] = df["traffic_type"].map(CAMPAIGN)
    df["tunnel"] = df["traffic_type"].map(TUNNEL)

    s = df.groupby(["traffic_type", "service"]).agg(
        flows=("session", "size"), sessions=("session", "nunique"))
    s["largest_session_share"] = (
        df.groupby(["traffic_type", "service", "session"]).size()
        .groupby(level=[0, 1]).max() / s["flows"]).round(2)
    log.append(f"### Sesje (przerwa > {args.gap_min:g} min = nowa sesja)\n\n{s.to_markdown()}\n")
    print(f"\n== Sesje (gap {args.gap_min:g} min)\n{s}")

    meta = ["traffic_type", "service", "campaign", "tunnel", "session", "ts",
            "Src IP", "Dst IP", "Src Port", "Dst Port"]
    out = df[meta + features].reset_index(drop=True)
    out[features] = out[features].astype("float64")
    features_json = json.dumps(
        {"features": features, "dropped_constant": const, "session_gap_min": args.gap_min},
        indent=2, ensure_ascii=False)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    out.to_parquet(args.out_dir / "flows.parquet", index=False)
    (args.out_dir / "features.json").write_text(features_json, encoding="utf-8")
    # Kopia listy cech w repozytorium - mała, potrzebna aplikacji i do odtwarzalności.
    (args.reports_dir / "features.json").write_text(features_json, encoding="utf-8")
    (args.reports_dir / "preprocess_report.md").write_text(
        "# Raport z przygotowania danych\n\n" + "\n".join(log), encoding="utf-8")
    print(f"\nZapisano {len(out):,} przepływów -> {args.out_dir / 'flows.parquet'}")


if __name__ == "__main__":
    main()
