"""Modele i siatki hiperparametrów (plan §5.2, schemat oceny: docs/decyzje.md, etap 03a)."""
from dataclasses import dataclass
from typing import Any, Callable

from sklearn.base import ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

SEED = 42


@dataclass(frozen=True)
class ModelSpec:
    name: str
    make: Callable[[int], ClassifierMixin]
    grid: dict[str, list[Any]]

    def pipeline(self, seed: int = SEED) -> Pipeline:
        """Skalowanie i model w jednym potoku, żeby test nie wpływał na skalowanie."""
        return Pipeline([("scale", StandardScaler()), ("clf", self.make(seed))])

    def param_grid(self) -> dict[str, list[Any]]:
        return {f"clf__{k}": v for k, v in self.grid.items()}


MODELS: dict[str, ModelSpec] = {
    # stratified, bo przy most_frequent F1 makro jest z definicji bardzo niska
    "dummy": ModelSpec(
        "dummy", lambda seed: DummyClassifier(strategy="stratified", random_state=seed), {}
    ),
    "knn": ModelSpec(
        "knn",
        lambda seed: KNeighborsClassifier(),
        {"n_neighbors": [3, 5, 11, 21, 41], "weights": ["uniform", "distance"],
         "metric": ["euclidean", "manhattan"]},
    ),
    "tree": ModelSpec(
        "tree",
        lambda seed: DecisionTreeClassifier(class_weight="balanced", random_state=seed),
        {"max_depth": [5, 10, 20, None], "min_samples_leaf": [1, 5, 20],
         "criterion": ["gini", "entropy"]},
    ),
    # n_jobs=1: równolegle liczy GridSearchCV, a zagnieżdżone wątki tylko by konkurowały
    "rf": ModelSpec(
        "rf",
        lambda seed: RandomForestClassifier(
            n_estimators=200, class_weight="balanced", n_jobs=1, random_state=seed),
        {"max_depth": [10, 20, None], "max_features": ["sqrt", 0.3],
         "min_samples_leaf": [1, 5]},
    ),
}


def get_model(name: str) -> ModelSpec:
    if name not in MODELS:
        raise KeyError(f"Nieznany model {name!r}; dostępne: {sorted(MODELS)}")
    return MODELS[name]
