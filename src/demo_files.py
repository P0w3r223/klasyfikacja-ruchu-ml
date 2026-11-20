"""Pliki do pokazu w app/demo/ (etap 09): sesje odłożone w etapie 05 wycięte z Darknet.CSV.

Każdy plik obejmuje jedną kampanię nagrań. Zawiera przepływy sesji odłożonych
(`metadata.json` → `holdout.sessions`, model ich nie widział) i trochę ruchu tła tego
samego hosta z tych samych okien czasowych, żeby na pokazie było widać filtr tła.
Przepływów tego hosta z innymi adresami nie bierzemy, bo należą do sesji z treningu.
Do tego kopiujemy pliki E7 (USBVPN2022) z reports/results/06_e7/demo/.

Uruchamia się tylko na komputerze z surowym Darknet.CSV (Release data-raw-v1).

Użycie: python src/demo_files.py [--raw PLIK] [--out-dir KATALOG] [--max-background 10]
"""
import argparse
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

import model_store
import preprocess as pp

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "app" / "demo"
E7_DEMO_DIR = ROOT / "reports" / "results" / "06_e7" / "demo"
E7_FILES = ["usbvpn2022_www_video.csv", "usbvpn2022_voip_video.csv"]
CAMPAIGN_FILES = {"tor-nontor": "darknet_tor_www_video.csv",
                  "vpn-nonvpn": "darknet_vpn_voip_video.csv"}
RAW_TS_FORMAT = "%d/%m/%Y %I:%M:%S %p"  # Timestamp w Darknet.CSV (match_rules → ts)
SEED = 42


def raw_timestamps(raw: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(raw["Timestamp"], format=RAW_TS_FORMAT)


def session_mask(raw: pd.DataFrame, ts: pd.Series, pair: pd.Series,
                 session: dict[str, Any]) -> pd.Series:
    """Przepływy jednej sesji odłożonej według `holdout.match_rules`."""
    return ((raw["traffic_type"] == session["traffic_type"])
            & (raw["service"] == session["service"])
            & (pair == f"{session['ip_a']}|{session['ip_b']}")
            & ts.between(pd.Timestamp(session["ts_min"]), pd.Timestamp(session["ts_max"])))


def background_mask(raw: pd.DataFrame, ts: pd.Series, reason: pd.Series,
                    session: dict[str, Any]) -> pd.Series:
    """Ruch tła hostów sesji (dowolny drugi adres) w jej oknie czasowym."""
    hosts = {session["ip_a"], session["ip_b"]}
    return ((raw["traffic_type"] == session["traffic_type"])
            & (raw["Src IP"].isin(hosts) | raw["Dst IP"].isin(hosts))
            & ts.between(pd.Timestamp(session["ts_min"]), pd.Timestamp(session["ts_max"]))
            & (reason != ""))


def clean_index(raw: pd.DataFrame) -> pd.Index:
    """Wiersze, które zostają w flows.parquet (kroki preprocess.build bez sesji).

    Duplikaty są usuwane w całym zbiorze, więc przepływ z okna sesji może być kopią
    przepływu z treningu; takie wiersze nie trafiają do pliku demo.
    """
    subset = raw[raw["traffic_type"].isin(pp.TRAFFIC_TYPES) & raw["service"].notna()]
    kept, _ = pp.filter_background(subset)
    clean, _ = pp.drop_invalid_and_duplicates(kept, pp.feature_columns(kept))
    return clean.index


def select_demo_rows(raw: pd.DataFrame, sessions: list[dict[str, Any]],
                     max_background: int, seed: int = SEED) -> pd.DataFrame:
    """Wiersze surowego pliku: przepływy sesji odłożonych (te same co w flows.parquet)
    i najwyżej `max_background` przepływów tła na sesję, w kolejności czasu.
    `raw` jak z preprocess.load_raw."""
    ts, pair, reason = raw_timestamps(raw), pp.ip_pair(raw), pp.background_reason(raw)
    in_flows = raw.index.isin(clean_index(raw))
    picked: list[pd.Index] = []
    for session in sessions:
        hit = raw.index[session_mask(raw, ts, pair, session) & in_flows]
        got = len(hit)
        if got != session["n_flows"]:
            raise ValueError(f"Sesja {session} daje {got} przepływów zamiast "
                             f"{session['n_flows']}; inny Darknet.CSV niż przy treningu?")
        background = raw.loc[background_mask(raw, ts, reason, session)]
        n = min(max_background, len(background))
        picked += [hit, background.sample(n=n, random_state=seed).index]
    index = pd.Index(sorted(set().union(*picked)))
    order = ts[index].sort_values(kind="stable").index
    return raw.loc[order]


def to_raw_columns(rows: pd.DataFrame) -> pd.DataFrame:
    """Odwraca nazwy z load_raw; obie kolumny etykiet nazywają się `Label` jak w Darknet.CSV."""
    out = rows.drop(columns=["service"]).rename(
        columns={"traffic_type": "Label", "service_raw": "Label.1"})
    out.columns = ["Label" if c == "Label.1" else c for c in out.columns]
    return out.reset_index(drop=True)


def check_demo_file(path: Path, metadata: dict[str, Any]) -> None:
    columns = list(pd.read_csv(path, nrows=0).columns)
    missing = model_store.missing_input_columns(columns, metadata, require_label=True)
    if missing:
        raise ValueError(f"{path.name}: brak kolumn {missing}")


def write_demo_files(raw: pd.DataFrame, metadata: dict[str, Any], out_dir: Path,
                     max_background: int) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sessions = metadata["holdout"]["sessions"]
    written = []
    for campaign, name in CAMPAIGN_FILES.items():
        chosen = [s for s in sessions if s["campaign"] == campaign]
        if not chosen:
            raise ValueError(f"Brak sesji odłożonych w kampanii {campaign}")
        path = out_dir / name
        to_raw_columns(select_demo_rows(raw, chosen, max_background)).to_csv(path, index=False)
        written.append(path)
    for name in E7_FILES:
        written.append(Path(shutil.copyfile(E7_DEMO_DIR / name, out_dir / name)))
    for path in written:
        check_demo_file(path, metadata)
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, default=pp.RAW)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--max-background", type=int, default=10,
                    help="najwięcej przepływów tła na sesję")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    metadata = model_store.load_metadata()
    paths = write_demo_files(pp.load_raw(args.raw), metadata, args.out_dir, args.max_background)
    for path in paths:
        n = sum(1 for _ in path.open(encoding="utf-8")) - 1
        print(f"{path.relative_to(ROOT)}: {n} przepływów, {path.stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
