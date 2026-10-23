"""Potoki z models/ według models/metadata.json (etap 05; korzysta z tego też aplikacja).

Plik .joblib wczytuje się poprawnie tylko przy tych samych wersjach bibliotek co w treningu,
więc różnica wersji, inna suma SHA-256 albo ostrzeżenie przy wczytaniu przerywa pracę.
"""
import hashlib
import json
import platform
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
METADATA_FILE = "metadata.json"


def library_versions() -> dict[str, str]:
    return {"python": platform.python_version(), "sklearn": sklearn.__version__,
            "pandas": pd.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
            "joblib": joblib.__version__}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_mismatches(expected: dict[str, str], actual: dict[str, str]) -> dict[str, tuple]:
    """Różnice wersji; Pythona porównujemy do wersji podrzędnej (3.13), bo poprawki nie
    zmieniają formatu pickle, a obie maszyny mogą mieć inną poprawkę."""
    def comparable(name: str, version: str | None) -> str | None:
        return ".".join(version.split(".")[:2]) if name == "python" and version else version
    return {name: (want, actual.get(name)) for name, want in expected.items()
            if comparable(name, want) != comparable(name, actual.get(name))}


def load_metadata(models_dir: Path = MODELS_DIR) -> dict[str, Any]:
    path = models_dir / METADATA_FILE
    if not path.exists():
        raise FileNotFoundError(f"Brak {path}; pobierz Release z modelami "
                                "(docs/srodowisko.md)")
    return json.loads(path.read_text(encoding="utf-8"))


def check_versions(metadata: dict[str, Any]) -> None:
    mismatches = version_mismatches(metadata["versions"], library_versions())
    if mismatches:
        details = ", ".join(f"{k}: model {w}, tu {a}" for k, (w, a) in mismatches.items())
        raise RuntimeError(f"Inne wersje bibliotek niż przy treningu ({details}); "
                           "zainstaluj requirements.txt")


def load_pipeline(entry: dict[str, Any], models_dir: Path = MODELS_DIR) -> Pipeline:
    """Wczytuje jeden potok z metadata["pipelines"]; ostrzeżenie przy wczytaniu to błąd."""
    path = models_dir / entry["file"]
    if not path.exists():
        raise FileNotFoundError(f"Brak {path}; pobierz Release z modelami (docs/srodowisko.md)")
    actual = file_sha256(path)
    if actual != entry["sha256"]:
        raise ValueError(f"{path.name}: SHA-256 {actual} różni się od metadata.json "
                         f"({entry['sha256']}); pobierz plik ponownie z --clobber")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return joblib.load(path)


def find_pipeline(metadata: dict[str, Any], task: str, model: str) -> dict[str, Any]:
    for entry in metadata["pipelines"]:
        if entry["task"] == task and entry["model"] == model:
            return entry
    available = sorted((e["task"], e["model"]) for e in metadata["pipelines"])
    raise KeyError(f"Brak potoku {task}/{model}; dostępne: {available}")
