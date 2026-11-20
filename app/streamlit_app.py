"""Klasyfikacja ruchu sieciowego: WWW, VoIP, Video (pokaz projektu, etap 09).

Uruchomienie z katalogu repozytorium: streamlit run app/streamlit_app.py
Potrzebne są modele z Release models-v1 w models/ (docs/srodowisko.md).
"""
import io
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import app_logic  # noqa: E402  (src/ dopiero po dodaniu do ścieżki)
import model_store  # noqa: E402

DEMO_DIR = ROOT / "app" / "demo"
MODEL_NAMES = {"knn": "k-NN", "tree": "drzewo decyzyjne", "rf": "Random Forest"}
SHOWN_COLUMNS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Protocol", "Timestamp"]
TOP_FEATURES = 10


def fmt(x: float, digits: int = 3) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


@st.cache_resource
def load_metadata() -> dict[str, Any]:
    metadata = model_store.load_metadata()
    model_store.check_versions(metadata)
    return metadata


@st.cache_resource
def load_pipeline(task: str, model: str) -> Pipeline:
    metadata = load_metadata()
    return model_store.load_pipeline(model_store.find_pipeline(metadata, task, model))


@st.cache_data(max_entries=3)  # wgrane pliki trzymamy w pamięci, więc tylko kilka ostatnich
def read_csv_bytes(data: bytes) -> pd.DataFrame:
    return app_logic.read_flows_csv(io.BytesIO(data))


@st.cache_data
def read_csv_path(path: str, mtime_ns: int) -> pd.DataFrame:
    """`mtime_ns` jest tylko kluczem cache: po zmianie pliku demo wczytujemy go ponownie."""
    return app_logic.read_flows_csv(path)


@st.cache_data(show_spinner=False)
def permutation_ranking(task: str, model: str, X: pd.DataFrame, y: pd.Series,
                        classes: list[str]) -> pd.Series:
    return app_logic.file_permutation_importance(load_pipeline(task, model), X, y, classes)


def choose_input() -> tuple[str, pd.DataFrame] | None:
    source = st.sidebar.radio("Dane", ["Plik do pokazu", "Własny plik CSV"])
    if source == "Plik do pokazu":
        files = sorted(DEMO_DIR.glob("*.csv"))
        if not files:
            st.sidebar.warning(f"Brak plików w {DEMO_DIR.relative_to(ROOT)}")
            return None
        path = st.sidebar.selectbox("Plik", files, format_func=lambda p: p.name)
        return path.name, read_csv_path(str(path), path.stat().st_mtime_ns)
    uploaded = st.sidebar.file_uploader("CSV w formacie Darknet.CSV (CICFlowMeter)",
                                        type="csv")
    if uploaded is None:
        return None
    return uploaded.name, read_csv_bytes(uploaded.getvalue())


def choose_model(metadata: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    tasks = metadata["tasks"]
    task = st.sidebar.selectbox("Zadanie", list(tasks),
                                format_func=lambda t: f"{tasks[t]['title']} ({tasks[t]['role']})")
    models = [e["model"] for e in metadata["pipelines"] if e["task"] == task]
    model = st.sidebar.selectbox("Model", models, index=len(models) - 1,
                                 format_func=lambda m: MODEL_NAMES.get(m, m))
    return task, model, model_store.find_pipeline(metadata, task, model)


def show_task(metadata: dict[str, Any], task: str, entry: dict[str, Any]) -> None:
    info = metadata["tasks"][task]
    note = st.info if info["role"] == "główne" else st.warning
    note(f"**{info['title']}**, zadanie {info['role']}. {info['description']}")
    cv = entry["reported_cv"]
    st.caption(f"Model: {MODEL_NAMES.get(entry['model'], entry['model'])}, "
               f"parametry {entry['best_params']}. F1 (makro) w walidacji krzyżowej po sesjach: "
               f"{fmt(cv['f1_macro_mean'])} ± {fmt(cv['f1_macro_std'])}. "
               f"Zestaw cech: {metadata['feature_set']} ({len(metadata['features'])} cech).")


def show_input_summary(prepared: app_logic.PreparedInput) -> None:
    cols = st.columns(4)
    cols[0].metric("Przepływy w pliku", prepared.n_read)
    cols[1].metric("Ruch tła (usunięty)", int(prepared.removed_background.sum()))
    cols[2].metric("Wiersze z inf/NaN (usunięte)", prepared.removed_invalid)
    cols[3].metric("Sklasyfikowane", len(prepared.flows))
    if not prepared.removed_background.empty:
        with st.expander("Ruch tła według przyczyny (ten sam filtr co przy treningu)"):
            st.dataframe(prepared.removed_background.rename("przepływy"))


def show_predictions(prepared: app_logic.PreparedInput, predicted: pd.DataFrame,
                     classes: list[str]) -> None:
    st.subheader("Rozkład klas")
    st.bar_chart(app_logic.class_distribution(predicted["klasa"], classes).rename("przepływy"),
                 sort=False)
    st.subheader("Klasa każdego przepływu")
    table = prepared.flows[[c for c in SHOWN_COLUMNS if c in prepared.flows.columns]]
    if prepared.y is not None:
        table = table.assign(etykieta=prepared.y.fillna("nieznana"))
    table = table.assign(**{"klasa modelu": predicted["klasa"], "pewność": predicted["pewność"]})
    st.dataframe(table, hide_index=True, column_config={
        "pewność": st.column_config.NumberColumn(format="%.2f")})


def show_evaluation(evaluation: app_logic.Evaluation | None) -> None:
    st.subheader("Ocena względem etykiet z pliku")
    if evaluation is None:
        st.info("Żaden przepływ nie ma etykiety spośród klas tego zadania.")
        return
    cols = st.columns(1 + len(evaluation.f1_per_class))
    cols[0].metric("F1 (makro)", fmt(evaluation.f1_macro))
    for col, (cls, f1) in zip(cols[1:], evaluation.f1_per_class.items()):
        col.metric(f"F1 {cls}", fmt(f1))
    st.dataframe(evaluation.confusion.style.background_gradient(cmap="Blues", axis=None))
    st.caption(f"Ocena na {evaluation.n_evaluated} przepływach z etykietą spośród klas zadania.")
    if evaluation.absent_classes:
        st.warning(f"W pliku nie ma etykiet klasy {', '.join(evaluation.absent_classes)}: F1 "
                   "(makro) to średnia po pozostałych klasach, nieporównywalna z walidacją.")
    if not evaluation.outside_classes.empty:
        outside = ", ".join(f"{k}: {v}" for k, v in evaluation.outside_classes.items())
        st.caption(f"Poza oceną (etykieta spoza klas zadania): {outside}.")


def show_importance(task: str, model: str, prepared: app_logic.PreparedInput,
                    classes: list[str]) -> None:
    st.subheader("Najważniejsze cechy")
    builtin = app_logic.builtin_importance(load_pipeline(task, model))
    if builtin is not None:
        st.caption("Ważność Gini z modelu (z treningu, niezależna od pliku).")
        st.bar_chart(builtin.head(TOP_FEATURES).rename("ważność"), horizontal=True, sort=False)
        return
    if prepared.y is None or not prepared.y.isin(classes).any():
        st.info("k-NN nie ma wbudowanej ważności cech. Ważność permutacyjną liczymy tylko "
                "dla pliku z etykietami spośród klas zadania.")
        return
    n = min(int(prepared.y.isin(classes).sum()), app_logic.PERMUTATION_MAX_FLOWS)
    with st.spinner("Liczę ważność permutacyjną (k-NN)…"):
        ranking = permutation_ranking(task, model, prepared.X, prepared.y, classes)
    st.caption(f"Ważność permutacyjna na tym pliku: spadek F1 (makro) po przetasowaniu cechy, "
               f"{app_logic.PERMUTATION_REPEATS} powtórzeń, {n} przepływów.")
    if n < app_logic.SMALL_SAMPLE_FLOWS:
        st.warning(f"Tylko {n} przepływów z etykietą: kolejność cech jest bardzo niepewna.")
    st.bar_chart(ranking.head(TOP_FEATURES).rename("spadek F1"), horizontal=True, sort=False)


def main() -> None:
    st.set_page_config(page_title="Klasyfikacja ruchu", layout="wide")
    st.title("Klasyfikacja ruchu sieciowego: WWW, VoIP, Video")
    try:
        metadata = load_metadata()
    except (FileNotFoundError, RuntimeError) as exc:
        st.error(str(exc))
        st.stop()
    task, model, entry = choose_model(metadata)
    try:
        pipeline = load_pipeline(task, model)
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
    show_task(metadata, task, entry)
    try:
        chosen = choose_input()
        if chosen is None:
            st.info("Wybierz plik do pokazu albo wgraj własny CSV w panelu po lewej.")
            return
        name, df = chosen
        prepared = app_logic.prepare_input(df, metadata)
    except app_logic.InputError as exc:
        st.error(str(exc))
        return
    classes = list(entry["classes"])
    predicted = app_logic.predict(pipeline, prepared.X)
    st.header(name)
    show_input_summary(prepared)
    show_predictions(prepared, predicted, classes)
    if prepared.y is not None:
        show_evaluation(app_logic.evaluate(prepared.y, predicted["klasa"], classes))
    show_importance(task, model, prepared, classes)


main()
