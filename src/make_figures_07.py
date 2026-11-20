"""Rysunek etapu 07 (E6, P4): wynik w funkcji liczby pierwszych pakietów przepływu.

    python src/make_figures_07.py

Czyta reports/results/07_e6/ocena/summary.csv (`e6_ocena.py`); nic nie trenuje.
Wiersze: populacje (wszystkie przepływy, przepływy z ≥ 20 pakietami), kolumny: F1 makro
i dokładność zbalansowana. Linia przerywana w kolorze modelu to pełny przepływ. Dummy (poziom
zgadywania, ok. 0,5) jest tylko w podpisie i tabeli, bo zajmowałby pół skali.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from e6 import FULL_FLOW, RESULTS  # noqa: E402
from make_figures_03b import (INK, INK_MUTED, MODEL_LABELS, _num, _style_axes,  # noqa: E402
                              save_figures)

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "reports" / "figures"
FIGURE_NAME = "15_e6_pierwsze_pakiety.png"
# kolejność i kolory jak w rysunkach 12–13
MODEL_STYLE = {"knn": ("#2a78d6", "o"), "tree": ("#eb6834", "s"), "rf": ("#1baf7a", "D")}
# przesunięcie w poziomie (mnożnik na osi logarytmicznej), żeby słupki błędów się nie zakrywały
DODGE = {"knn": 0.94, "tree": 1.0, "rf": 1.06}
Y_LIMITS = (0.8, 1.005)
POPULATION_LABELS = {"wszystkie": "wszystkie przepływy (krótsze niż N: wszystkie pakiety)",
                     "min20": "przepływy z ≥ 20 pakietami"}
METRIC_LABELS = {"f1_macro": "F1 makro", "balanced_accuracy": "dokładność zbalansowana"}


def model_curves(summary: pd.DataFrame, population: str, metric: str
                 ) -> dict[str, tuple[pd.DataFrame, float]]:
    """Model → (punkty N: n_first, średnia, odchylenie; wartość dla pełnego przepływu)."""
    part = summary[summary["population"] == population]
    out = {}
    for model in MODEL_STYLE:
        m = part[part["model"] == model]
        if m.empty:
            continue
        full = m.loc[m["n_first"] == FULL_FLOW, f"{metric}_mean"]
        if len(full) != 1:
            raise ValueError(f"{population}/{model}: brak wiersza pełnego przepływu")
        points = (m[m["n_first"] != FULL_FLOW].sort_values("n_first")
                  [["n_first", f"{metric}_mean", f"{metric}_std"]])
        out[model] = (points.set_axis(["n", "mean", "std"], axis=1), float(full.iloc[0]))
    return out


def draw_panel(ax: plt.Axes, curves: dict[str, tuple[pd.DataFrame, float]]) -> None:
    for model, (pts, full) in curves.items():
        color, marker = MODEL_STYLE[model]
        ax.axhline(full, color=color, linewidth=1.2, linestyle=(0, (4, 3)), alpha=0.9)
        ax.errorbar(pts["n"] * DODGE[model], pts["mean"], yerr=pts["std"], color=color, marker=marker,
                    markersize=7, linewidth=2, capsize=3, elinewidth=1,
                    markeredgecolor="white", markeredgewidth=1, label=MODEL_LABELS[model])
    ax.set_xscale("log")
    ns = sorted({n for pts, _ in curves.values() for n in pts["n"]})
    ax.set_xticks(ns, [str(n) for n in ns])
    ax.minorticks_off()
    _style_axes(ax)
    ax.set_ylim(*Y_LIMITS)
    ax.set_yticks([0.80, 0.85, 0.90, 0.95, 1.00])


def dummy_note(summary: pd.DataFrame) -> str:
    d = summary[summary["model"] == "dummy"]
    if d.empty:
        return ""
    lo, hi = d[["f1_macro_mean", "balanced_accuracy_mean"]].stack().agg(["min", "max"])
    return f"; Dummy (zgadywanie): {_num(lo, 2)}–{_num(hi, 2)}"


def e6_figure(summary: pd.DataFrame) -> plt.Figure:
    populations = [p for p in POPULATION_LABELS if p in set(summary["population"])]
    fig, axes = plt.subplots(len(populations), len(METRIC_LABELS), figsize=(10, 4 * len(populations)),
                             squeeze=False, sharey=True)
    for row, pop in enumerate(populations):
        for col, metric in enumerate(METRIC_LABELS):
            ax = axes[row][col]
            draw_panel(ax, model_curves(summary, pop, metric))
            ax.set_title(f"{METRIC_LABELS[metric]} · {POPULATION_LABELS[pop]}", fontsize=9.5,
                         color=INK, loc="left")
            ax.set_xlabel("liczba pierwszych pakietów przepływu N", color=INK_MUTED)
    handles, labels = axes[0][0].get_legend_handles_labels()
    handles.append(plt.Line2D([], [], color=INK_MUTED, linestyle=(0, (4, 3)), linewidth=1.2))
    labels.append("pełny przepływ (kolor modelu)")
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.suptitle("E6: VoIP vs Video z pierwszych N pakietów (VPN-nonVPN, podział po sesjach, "
                 f"średnia ± odchylenie po foldach{dummy_note(summary)})", y=1.04, fontsize=10.5,
                 color=INK)
    fig.tight_layout()
    return fig


SAVE_KW = {"dpi": 150, "bbox_inches": "tight"}


def figures(e6_results: Path) -> dict[str, plt.Figure]:
    """Rysunek 15 z reports/results/07_e6; niczego nie zapisuje."""
    return {FIGURE_NAME: e6_figure(pd.read_csv(e6_results / "ocena" / "summary.csv"))}


def main() -> None:
    save_figures(figures(RESULTS), FIGURES, **SAVE_KW)
    print(f"Rysunek: {FIGURE_NAME}")


if __name__ == "__main__":
    sys.exit(main())
