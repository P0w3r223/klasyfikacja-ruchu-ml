"""E7, krok 2: potoki z models-v1 na USBVPN2022, tylko test (bez treningu i strojenia).

Funkcje bez I/O; zapis i CLI są w src/e7.py (`python src/e7.py ocena`).
"""
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             f1_score, precision_recall_fscore_support)

# Odniesienia Darknet z ks_cechy.csv (e7.references), na których uczyło się każde zadanie.
# Potok VoIP vs Video widział też ruch VPN, ale KS liczymy względem ruchu zwykłego, bo
# USBVPN2022 w E7 to tylko pliki „Non VPN”.
TASK_REFERENCES: dict[str, dict[str, list[str]]] = {
    "www_video_tor": {"WWW": ["WWW (Tor-nonTor)"], "Video": ["Video (Tor-nonTor)"]},
    "voip_video_vpncamp": {"VoIP": ["VoIP (VPN-nonVPN)"], "Video": ["Video (VPN-nonVPN)"]},
    "uslugi3_plain": {"WWW": ["WWW (Tor-nonTor)"], "VoIP": ["VoIP (VPN-nonVPN)"],
                      "Video": ["Video (Tor-nonTor)", "Video (VPN-nonVPN)"]},
}
SHORT_FLOW_MAX, LONG_FLOW_MIN = 3, 21  # pakiety: ≤ 3 to próba połączenia, ≥ 21 to transfer
WEB_PORTS = {443: "443", 80: "80"}


def task_population(usb: pd.DataFrame, classes: list[str]) -> pd.DataFrame:
    missing = [c for c in classes if not (usb["service"] == c).any()]
    if missing:
        raise ValueError(f"USBVPN2022 nie ma przepływów klas {missing}")
    return usb[usb["service"].isin(classes)]


def metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str]) -> dict[str, Any]:
    """F1 makro, dokładność zbalansowana i miary per klasa; macierz: wiersze = prawda."""
    prec, rec, f1, n = precision_recall_fscore_support(y_true, y_pred, labels=classes,
                                                       zero_division=0)
    out: dict[str, Any] = {
        "f1_macro": f1_score(y_true, y_pred, labels=classes, average="macro", zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "accuracy": accuracy_score(y_true, y_pred),
        "confusion": confusion_matrix(y_true, y_pred, labels=classes).tolist()}
    for i, c in enumerate(classes):
        out |= {f"recall_{c}": rec[i], f"precision_{c}": prec[i], f"f1_{c}": f1[i],
                f"n_{c}": int(n[i])}
    return out


def majority_baseline(y_true: np.ndarray, classes: list[str]) -> float:
    """F1 makro stałej odpowiedzi „klasa większości” przy proporcjach klas z USBVPN2022."""
    values, counts = np.unique(y_true, return_counts=True)
    const = np.full(len(y_true), values[np.argmax(counts)])
    return f1_score(y_true, const, labels=classes, average="macro", zero_division=0)


def cv_reference(experiment_dir: Path, model: str, classes: list[str]) -> dict[str, float]:
    """Wynik CV z E4 (podział po sesjach): F1 makro ± odchylenie i czułość z macierzy łącznej."""
    summary = pd.read_csv(experiment_dir / "summary.csv")
    row = summary[(summary["model"] == model) & (summary["split"] == "session")]
    if len(row) != 1:
        raise ValueError(f"{experiment_dir}: brak jednego wiersza {model}/session w summary.csv")
    conf = json.loads((experiment_dir / "confusion.json").read_text(encoding="utf-8"))
    entry = conf[f"{model}/session"]
    total = np.asarray(entry["total"], dtype=float)
    recall = dict(zip(entry["classes"], np.diag(total) / total.sum(axis=1)))
    return {"f1_macro": float(row["f1_macro_mean"].iloc[0]),
            "f1_macro_std": float(row["f1_macro_std"].iloc[0]),
            **{f"recall_{c}": float(recall[c]) for c in classes}}


def flow_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Cechy przepływu do rozbicia błędów: protokół, długość w pakietach, port usługi."""
    n = df["Total Fwd Packet"] + df["Total Bwd packets"]
    length = np.select([n <= SHORT_FLOW_MAX, n >= LONG_FLOW_MIN],
                       [f"≤ {SHORT_FLOW_MAX} pakiety", f"≥ {LONG_FLOW_MIN} pakietów"],
                       f"{SHORT_FLOW_MAX + 1}–{LONG_FLOW_MIN - 1} pakietów")
    port = pd.Series("inny", index=df.index)
    for p, name in WEB_PORTS.items():
        port = port.mask((port == "inny") & ((df["Dst Port"] == p) | (df["Src Port"] == p)), name)
    proto = df["Protocol"].map({6.0: "TCP", 17.0: "UDP"}).fillna("inny")
    return pd.DataFrame({"protokół": proto, "długość": length, "port": port}, index=df.index)


def recall_breakdown(df: pd.DataFrame, y_pred: np.ndarray, classes: list[str]) -> pd.DataFrame:
    """Czułość per klasa w każdym przedziale protokołu, długości i portu."""
    buckets = flow_buckets(df)
    frame = buckets.assign(service=df["service"].to_numpy(),
                           correct=df["service"].to_numpy() == y_pred)
    parts = [frame.groupby(["service", by])["correct"].agg(n="size", recall="mean")
             .reset_index().rename(columns={by: "value"}).assign(by=by)
             for by in buckets.columns]
    out = pd.concat(parts, ignore_index=True)[["by", "value", "service", "n", "recall"]]
    return out.sort_values(["by", "service", "value"]).reset_index(drop=True)


def feature_shift(importance: pd.Series, ks: pd.DataFrame, task: str) -> pd.DataFrame:
    """Ważność cechy w RF (Gini) obok KS USBVPN2022 vs Darknet dla klas zadania.

    `ks` to ks_cechy.csv z kroku 1; dla Video w zadaniu 3 usług KS to średnia z obu kampanii.
    Kolumna `shift_weighted` = ważność × średni KS klas, czyli ile przesunięcia trafia w cechy,
    na których model faktycznie się opiera.
    """
    out = pd.DataFrame({"importance": importance})
    for cls, refs in TASK_REFERENCES[task].items():
        sel = ks[ks["reference"].isin(refs)].groupby("feature")["ks"].mean()
        out[f"ks_{cls}"] = sel.reindex(out.index)
    if out.isna().any().any():
        missing = out.index[out.isna().any(axis=1)].tolist()
        raise ValueError(f"Brak KS dla cech {missing}; uruchom najpierw `e7.py rozklady`")
    ks_cols = [c for c in out.columns if c.startswith("ks_")]
    out["ks_mean"] = out[ks_cols].mean(axis=1)
    out["shift_weighted"] = out["importance"] * out["ks_mean"]
    return out.sort_values("importance", ascending=False)


MODEL_NAMES = {"knn": "k-NN", "tree": "drzewo", "rf": "RF"}


def _pct(x: float) -> str:
    return f"{100 * x:.1f}"


def _metrics_table(res: pd.DataFrame, task: str, classes: list[str]) -> list[str]:
    head = ("| model | F1 makro CV E4 | F1 makro USBVPN2022 | zmiana | dokł. zbalansowana | "
            + " | ".join(f"czułość {c}: CV → USBVPN [%]" for c in classes) + " |")
    lines = [head, "| --- | ---: | ---: | ---: | ---: | " + " | ".join("---:" for _ in classes)
             + " |"]
    for r in res[res["task"] == task].itertuples(index=False):
        row = r._asdict()
        recalls = " | ".join(f"{_pct(row[f'cv_recall_{c}'])} → {_pct(row[f'recall_{c}'])}"
                             for c in classes)
        lines.append(f"| {MODEL_NAMES[r.model]} | {r.cv_f1_macro:.3f} ± {r.cv_f1_macro_std:.3f} "
                     f"| {r.f1_macro:.3f} | {r.f1_macro - r.cv_f1_macro:+.3f} | "
                     f"{r.balanced_accuracy:.3f} | {recalls} |")
    first = res[res["task"] == task].iloc[0]
    counts = ", ".join(f"{c} {int(first[f'n_{c}']):,}" for c in classes)
    lines += ["", f"Przepływy USBVPN2022: {counts}. Stała odpowiedź „klasa większości” daje "
              f"F1 makro {first['f1_macro_majority']:.3f}, dokładność zbalansowana "
              f"{1 / len(classes):.3f}."]
    return lines


def _breakdown_table(breakdown: pd.DataFrame, task: str, model: str,
                     classes: list[str]) -> list[str]:
    b = breakdown[(breakdown["task"] == task) & (breakdown["model"] == model)]
    lines = ["| podział | wartość | " + " | ".join(f"{c}: czułość % (n)" for c in classes) + " |",
             "| --- | --- | " + " | ".join("---:" for _ in classes) + " |"]
    for (by, value), g in b.groupby(["by", "value"], sort=True):
        cells = []
        for c in classes:
            hit = g[g["service"] == c]
            cells.append(f"{_pct(hit['recall'].iloc[0])} ({int(hit['n'].iloc[0]):,})"
                         if len(hit) else "–")
        lines.append(f"| {by} | {value} | " + " | ".join(cells) + " |")
    return lines


def _shift_table(shift: pd.DataFrame, task: str, classes: list[str], top: int) -> list[str]:
    s = shift[shift["task"] == task]
    weighted = s["shift_weighted"].sum() / s["importance"].sum()
    lines = [f"Średni KS ważony ważnością RF: **{weighted:.2f}** (bez ważenia "
             f"{s['ks_mean'].mean():.2f}).", "",
             "| cecha | ważność RF | " + " | ".join(f"KS {c}" for c in classes) + " |",
             "| --- | ---: | " + " | ".join("---:" for _ in classes) + " |"]
    for f, r in s.head(top).iterrows():
        lines.append(f"| {f} | {r['importance']:.3f} | "
                     + " | ".join(f"{r[f'ks_{c}']:.2f}" for c in classes) + " |")
    return lines


def ocena_markdown(res: pd.DataFrame, breakdown: pd.DataFrame, shift: pd.DataFrame,
                   tasks: dict[str, Any], top: int = 10) -> str:
    lines = ["# E7, krok 2: modele z models-v1 na USBVPN2022 (ruch bez VPN)\n",
             "Tylko test: potoki uczone na CIC-Darknet2020 (zestaw `bez_skrotow`), bez treningu "
             "i strojenia na USBVPN2022. „CV E4” to wynik zagnieżdżonej CV po sesjach z E4 "
             "(`e4_bez_skrotow_*`), do którego odsyła `metadata.json`; czułość CV z łącznej "
             "macierzy pomyłek po foldach. Proporcje klas w USBVPN2022 są inne niż w Darknet, "
             "więc obok F1 makro podajemy dokładność zbalansowaną (średnia czułość klas), "
             "która od proporcji nie zależy.\n"]
    for task, spec in tasks.items():
        classes = spec["classes"]
        lines += [f"## {spec['title']}\n", *_metrics_table(res, task, classes), "",
                  "### Czułość RF według protokołu, długości przepływu i portu\n",
                  *_breakdown_table(breakdown, task, "rf", classes), "",
                  f"### Przesunięcie cech, na których opiera się RF (top {top} wg Gini)\n",
                  *_shift_table(shift, task, classes, top), ""]
    return "\n".join(lines) + "\n"
