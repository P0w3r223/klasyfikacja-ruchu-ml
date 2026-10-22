"""Wczytywanie przetworzonych danych i podział cech na grupy (P1, E4)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FEATURES_JSON = ROOT / "reports" / "features.json"

SERVICES = ["WWW", "VoIP", "Video"]


def feature_list() -> list[str]:
    return json.loads(FEATURES_JSON.read_text(encoding="utf-8"))["features"]


def built_session_gap_min() -> float:
    """Próg sesji (min), z którym preprocess.py zbudował kolumnę session."""
    return float(json.loads(FEATURES_JSON.read_text(encoding="utf-8"))["session_gap_min"])


def load_flows(include_audio: bool = False, path: Path | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path or PROCESSED / "flows.parquet")
    if not include_audio:
        df = df[df["service"] != "Audio"]
    return df.reset_index(drop=True)


def feature_group(name: str) -> str:
    """Grupa cechy: czasowe / rozmiarowe / tempo / liczności / TCP i protokół."""
    n = name.lower()
    if "init win" in n or "flag" in n or n in {"protocol", "fwd seg size min"}:
        return "tcp_protokol"
    if "/s" in n or "rate" in n:
        return "tempo"
    if "iat" in n or "idle" in n or n == "flow duration":
        return "czasowe"
    if any(k in n for k in ["length", "size", "bytes", "header"]):
        return "rozmiarowe"
    return "licznosci"


def feature_groups(features: list[str] | None = None) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for f in features or feature_list():
        groups.setdefault(feature_group(f), []).append(f)
    return groups
