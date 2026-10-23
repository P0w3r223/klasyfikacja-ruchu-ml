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
    """group_by: grupy podziału „session” (sesje z progiem session_gap_min)
    albo „ip_pair” (sama para IP, bez czasu i etykiety; opcja D w 03b).
    """
    name: str
    task: str
    models: tuple[str, ...]
    splits: tuple[str, ...]
    feature_set: str = "all"
    session_gap_min: float = 5.0
    group_by: str = "session"
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
    # etap 04, E3: warianty tunelu w kampanii VPN-nonVPN (mieszany to voip_video_vpncamp)
    Task("voip_video_plain", ("VoIP", "Video"),
         {"campaign": ("vpn-nonvpn",), "tunnel": ("plain",)}),
    Task("voip_video_vpn", ("VoIP", "Video"),
         {"campaign": ("vpn-nonvpn",), "tunnel": ("vpn",)}),
    # trening na całym ruchu zwykłym, foldy te same co w voip_video_vpn
    Task("voip_video_plain2vpn", ("VoIP", "Video"),
         {"campaign": ("vpn-nonvpn",), "tunnel": ("plain",)},
         test={"campaign": ("vpn-nonvpn",), "tunnel": ("vpn",)}),
]}

TASKS_03B = ("uslugi3_plain", "www_video_tor", "voip_video_vpncamp")
E3_TASKS = ("voip_video_plain", "voip_video_vpn", "voip_video_plain2vpn", "voip_video_vpncamp")

FEATURE_SETS: dict[str, Callable[[list[str]], list[str]]] = {
    "all": lambda features: list(features),
}

ALL_MODELS = ("dummy", "knn", "tree", "rf")

# Największa sesja VoIP w ruchu zwykłym ma 30% przepływów VoIP; przy 5 foldach jej fold
# dostaje tylko ją (1 sesja VoIP w teście). Przy 3 foldach: 20/22/7 sesji (etap 03b).
OUTER_FOLDS = {"uslugi3_plain": 3}

EXPERIMENTS: dict[str, Experiment] = {e.name: e for e in [
    Experiment("pilot_03a", "voip_video_vpncamp", ALL_MODELS, ("random", "session")),
    # etap 03b: E1/E2 i dwie analizy wrażliwości E2 (próg sesji, grupowanie po parze IP)
    *[Experiment(f"e1e2_{t}", t, ALL_MODELS, ("random", "session"),
                 n_outer=OUTER_FOLDS.get(t, 5)) for t in TASKS_03B],
    *[Experiment(f"e2_gap15_{t}", t, ALL_MODELS, ("session",), session_gap_min=15.0,
                 n_outer=OUTER_FOLDS.get(t, 5)) for t in TASKS_03B],
    *[Experiment(f"e2_ippair_{t}", t, ("dummy", "rf"), ("session",), group_by="ip_pair",
                 n_outer=OUTER_FOLDS.get(t, 5)) for t in TASKS_03B],
    # etap 04, E3: 3 foldy we wszystkich wariantach (decyzja autora), bo w ruchu zwykłym
    # przy 4–5 foldach największa sesja VoIP zostaje sama w foldzie; rozrzuty porównywalne
    *[Experiment(f"e3_{t}", t, ALL_MODELS, ("session",), n_outer=3) for t in E3_TASKS],
]}


def get_experiment(name: str) -> Experiment:
    if name not in EXPERIMENTS:
        raise KeyError(f"Nieznany eksperyment {name!r}; dostępne: {sorted(EXPERIMENTS)}")
    return EXPERIMENTS[name]
