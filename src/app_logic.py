"""Logika aplikacji Streamlit (etap 09), bez interfejsu: wejście, predykcja, ocena, ważność.

Wejście to CSV w formacie Darknet.CSV. Przepływy przechodzą ten sam filtr ruchu tła co
w preprocess.py (inaczej DNS czy LLMNR dostałyby etykietę jednej z usług), a cechy idą
do potoku w kolejności z `metadata.json` → `features`.
"""
from dataclasses import dataclass
from typing import IO, Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

import model_store
import preprocess as pp

PERMUTATION_REPEATS = 5
PERMUTATION_MAX_FLOWS = 200  # k-NN liczy odległości do całego zbioru treningowego
SMALL_SAMPLE_FLOWS = 100     # poniżej tej liczby ważność permutacyjna jest bardzo niepewna
SEED = 42


class InputError(ValueError):
    """Plik, którego nie da się sklasyfikować; komunikat jest dla użytkownika aplikacji."""


@dataclass(frozen=True)
class PreparedInput:
    flows: pd.DataFrame            # przepływy po filtrze tła i usunięciu inf/NaN (kolumny pliku)
    X: pd.DataFrame                # cechy w kolejności z metadata.json
    y: pd.Series | None            # usługa z kolumny etykiety (NaN: spoza SERVICE_MAP); None: brak
    n_read: int
    removed_background: pd.Series  # liczba usuniętych przepływów według przyczyny
    removed_invalid: int


@dataclass(frozen=True)
class Evaluation:
    confusion: pd.DataFrame        # wiersze: etykieta, kolumny: klasa modelu
    f1_macro: float
    f1_per_class: pd.Series
    n_evaluated: int
    outside_classes: pd.Series     # etykiety spoza klas zadania (poza oceną) i ich liczności


def read_flows_csv(source: str | IO[bytes]) -> pd.DataFrame:
    """CSV z przepływami; druga kolumna `Label` dostaje od pandas nazwę `Label.1`."""
    try:
        return pd.read_csv(source, low_memory=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        raise InputError(f"Nie udało się odczytać pliku jako CSV: {exc}") from exc


def prepare_input(df: pd.DataFrame, metadata: dict[str, Any]) -> PreparedInput:
    """Kontrola kolumn, filtr tła, usunięcie wierszy z inf/NaN; bez usuwania duplikatów,
    bo `Flow ID` i cechy mogą się w pliku powtarzać."""
    missing = model_store.missing_input_columns(list(df.columns), metadata)
    if missing:
        raise InputError(f"W pliku brakuje kolumn wymaganych przez model: {', '.join(missing)}")
    if df.empty:
        raise InputError("Plik nie zawiera żadnego przepływu")
    typed = df.assign(**{"Dst IP": df["Dst IP"].astype(str)})
    reason = pp.background_reason(typed)
    kept = typed[reason == ""]
    X = kept[metadata["features"]].apply(pd.to_numeric, errors="coerce")
    valid = np.isfinite(X.to_numpy(dtype=float)).all(axis=1)
    if not valid.any():
        raise InputError("Po odfiltrowaniu ruchu tła i wierszy z inf/NaN nie został "
                         "żaden przepływ do klasyfikacji")
    flows = kept[valid]
    label = metadata["label_column"]
    y = (flows[label].astype(str).str.strip().str.lower().map(pp.SERVICE_MAP)
         if label in flows.columns else None)
    return PreparedInput(flows=flows, X=X[valid].astype(float), y=y, n_read=len(df),
                         removed_background=reason[reason != ""].value_counts(),
                         removed_invalid=int((~valid).sum()))


def predict(pipeline: Pipeline, X: pd.DataFrame) -> pd.DataFrame:
    """Klasa każdego przepływu i pewność modelu (największe prawdopodobieństwo klasy)."""
    proba = pipeline.predict_proba(X)
    classes = pipeline.classes_
    return pd.DataFrame({"klasa": classes[proba.argmax(axis=1)],
                         "pewność": proba.max(axis=1)}, index=X.index)


def class_distribution(predicted: pd.Series, classes: list[str]) -> pd.Series:
    return predicted.value_counts().reindex(classes, fill_value=0)


def evaluate(y_true: pd.Series, y_pred: pd.Series, classes: list[str]) -> Evaluation | None:
    """Macierz pomyłek i F1 na przepływach z etykietą spośród klas zadania; None, gdy brak."""
    inside = y_true.isin(classes)
    outside = y_true[~inside].fillna("nieznana").value_counts()
    if not inside.any():
        return None
    t, p = y_true[inside], y_pred[inside]
    cm = confusion_matrix(t, p, labels=classes)
    per_class = f1_score(t, p, labels=classes, average=None, zero_division=0)
    return Evaluation(
        confusion=pd.DataFrame(cm, index=pd.Index(classes, name="etykieta"),
                               columns=pd.Index(classes, name="klasa modelu")),
        f1_macro=float(per_class.mean()),
        f1_per_class=pd.Series(per_class, index=classes),
        n_evaluated=int(inside.sum()), outside_classes=outside)


def builtin_importance(pipeline: Pipeline) -> pd.Series | None:
    """Ważność Gini z modelu (drzewo, RF) malejąco; None dla modeli bez niej (k-NN)."""
    model = pipeline[-1]
    if not hasattr(model, "feature_importances_"):
        return None
    imp = pd.Series(model.feature_importances_, index=pipeline.feature_names_in_)
    return imp.sort_values(ascending=False)


def file_permutation_importance(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series,
                                classes: list[str], seed: int = SEED) -> pd.Series:
    """Spadek F1 (makro) po przetasowaniu cechy, na przepływach pliku z etykietą z klas
    zadania; najwyżej PERMUTATION_MAX_FLOWS losowych przepływów."""
    inside = y.isin(classes)
    if not inside.any():
        raise InputError("Brak przepływów z etykietą spośród klas zadania")
    Xs, ys = X[inside], y[inside]
    if len(Xs) > PERMUTATION_MAX_FLOWS:
        Xs = Xs.sample(n=PERMUTATION_MAX_FLOWS, random_state=seed)
        ys = ys.loc[Xs.index]
    # Własna funkcja zamiast make_scorer: ten dla dwóch klas wymaga pos_label=1.
    def scorer(model: Pipeline, X_: pd.DataFrame, y_: pd.Series) -> float:
        return float(f1_score(y_, model.predict(X_), labels=classes, average="macro",
                              zero_division=0))

    result = permutation_importance(pipeline, Xs, ys, scoring=scorer,
                                    n_repeats=PERMUTATION_REPEATS, random_state=seed)
    return pd.Series(result.importances_mean, index=X.columns).sort_values(ascending=False)
