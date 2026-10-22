"""Rejestr zadań, zestawów cech i eksperymentów.

Etapy 03b–05 dopisują tu nowe wpisy; schemat oceny (evaluate.py) się nie zmienia.
"""
from dataclasses import dataclass
from typing import Callable

Filter = dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Task:
    """Zadanie klasyfikacji usług (kolumna service).

    train/test: dozwolone wartości kolumn meta; test=None oznacza tę samą
    populację co trening (zwykła CV). stratify_by: kolumny warstw w foldach.
    """
    name: str
    classes: tuple[str, ...]
    train: Filter
    test: Filter | None = None
    stratify_by: tuple[str, ...] = ("service",)


@dataclass(frozen=True)
class Experiment:
    name: str
    task: str
    models: tuple[str, ...]
    splits: tuple[str, ...]
    feature_set: str = "all"
    session_gap_min: float = 5.0
    n_outer: int = 5
    n_inner: int = 3
    n_repeats: int = 1
    seed: int = 42


TASKS: dict[str, Task] = {t.name: t for t in [
    # punkt odniesienia; Video z obu kampanii w każdym foldzie
    Task("uslugi3_plain", ("WWW", "VoIP", "Video"), {"tunnel": ("plain",)},
         stratify_by=("service", "campaign")),
    Task("www_video_tor", ("WWW", "Video"), {"campaign": ("tor-nontor",)}),
    # ruch zwykły i VPN razem; oba tunele w każdym foldzie
    Task("voip_video_vpncamp", ("VoIP", "Video"), {"campaign": ("vpn-nonvpn",)},
         stratify_by=("service", "tunnel")),
]}

FEATURE_SETS: dict[str, Callable[[list[str]], list[str]]] = {
    "all": lambda features: list(features),
}

ALL_MODELS = ("dummy", "knn", "tree", "rf")

EXPERIMENTS: dict[str, Experiment] = {e.name: e for e in [
    Experiment("pilot_03a", "voip_video_vpncamp", ALL_MODELS, ("random", "session")),
]}


def get_experiment(name: str) -> Experiment:
    if name not in EXPERIMENTS:
        raise KeyError(f"Nieznany eksperyment {name!r}; dostępne: {sorted(EXPERIMENTS)}")
    return EXPERIMENTS[name]
