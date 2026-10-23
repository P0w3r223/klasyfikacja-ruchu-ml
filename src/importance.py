"""Ważność grup cech (E4, P1): Gini zsumowany w grupach i permutacja całej grupy naraz."""
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from evaluate import FoldOutcome, Prepared
from features import feature_groups

N_PERMUTATIONS = 5


def gini_by_group(pipeline: Pipeline, groups: dict[str, list[str]]) -> dict[str, float]:
    """Suma feature_importances_ ostatniego kroku potoku w każdej grupie."""
    model = pipeline[-1]
    if not hasattr(model, "feature_importances_"):
        raise TypeError(f"{type(model).__name__} nie ma feature_importances_ (Gini)")
    imp = pd.Series(model.feature_importances_, index=pipeline.feature_names_in_)
    return {g: float(imp[cols].sum()) for g, cols in groups.items()}


def _f1(y_true: pd.Series, y_pred: np.ndarray, labels: tuple[str, ...]) -> float:
    return float(f1_score(y_true, y_pred, labels=list(labels), average="macro",
                          zero_division=0))


def group_permutation_importance(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series,
                                 labels: tuple[str, ...], groups: dict[str, list[str]],
                                 n_repeats: int = N_PERMUTATIONS,
                                 seed: int = 42) -> pd.DataFrame:
    """Spadek F1 makro, gdy wszystkie kolumny grupy dostają tę samą permutację wierszy.

    Permutowanie cech pojedynczo zaniża wkład grupy silnie skorelowanych cech
    (np. Flow IAT Mean i Fwd IAT Mean): model korzysta z kopii, której nie ruszono.
    """
    rng = np.random.default_rng(seed)
    base = _f1(y, pipeline.predict(X), labels)
    rows = []
    for group, cols in groups.items():
        drops = []
        for _ in range(n_repeats):
            permuted = X.copy()
            permuted[cols] = X[cols].to_numpy()[rng.permutation(len(X))]
            drops.append(base - _f1(y, pipeline.predict(permuted), labels))
        rows.append({"group": group, "n_features": len(cols), "f1_base": base,
                     "perm_mean": float(np.mean(drops)), "perm_std": float(np.std(drops))})
    return pd.DataFrame(rows)


def fold_importance(data: Prepared, out: FoldOutcome, seed: int = 42) -> pd.DataFrame:
    """Gini i ważność permutacyjna grup cech modelu z jednego foldu, liczona na jego teście."""
    groups = feature_groups(list(data.X.columns))
    perm = group_permutation_importance(
        out.fitted, data.X.iloc[out.test_idx], data.y.iloc[out.test_idx], data.classes,
        groups, seed=seed)
    return perm.assign(gini=perm["group"].map(gini_by_group(out.fitted, groups)))
