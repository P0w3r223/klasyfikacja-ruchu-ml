"""Tabele i rysunki etapu 04, część E4 (zestawy cech i ważność grup cech), z reports/results/.

    python src/make_figures_04_e4.py

Czyta gotowe wyniki eksperymentów e4_* (folds.csv, importance.csv) oraz e1e2_* z etapu
03b do porównania E1/E2 bez Idle *; nic nie trenuje. Zapisuje
reports/results/04_e4_tabela.md, 04_e4_folds.csv, 04_e4_importance.csv
i rysunki 13–14 w reports/figures/.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from experiments import E4_FEATURE_SETS, EXPERIMENTS, FEATURE_SETS  # noqa: E402
from features import feature_list  # noqa: E402
from make_figures_03b import (GRID, INK, INK_MUTED, MODEL_LABELS, MODEL_ORDER,  # noqa: E402
                              TASK_LABELS, TASK_ORDER, _num)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
FIGURES = ROOT / "reports" / "figures"

FEATURE_SET_ORDER = list(E4_FEATURE_SETS)
FEATURE_SET_LABELS = {
    "all": "wszystkie", "bez_idle": "bez Idle *", "bez_skrotow": "bez skrótów",
    "bez_protocol": "bez Idle * i Protocol", "tylko_czasowe": "tylko czasowe",
    "czasowe_tempo": "czasowe + tempo", "tylko_rozmiarowe": "tylko rozmiarowe"}
GROUP_LABELS = {"czasowe": "czasowe (IAT, Duration)", "rozmiarowe": "rozmiarowe",
                "tempo": "tempo (B/s, pakiety/s)", "licznosci": "liczności",
                "tcp_protokol": "TCP i protokół", "przeciek_czasu": "Idle * (przeciek czasu)"}
# ranking ważności na tych zestawach: z przeciekiem, bez niego i bez wszystkich skrótów
IMPORTANCE_SETS = ["all", "bez_idle", "bez_skrotow"]
TRAINED_MODELS = [m for m in MODEL_ORDER if m != "dummy"]
# kolejność barw stała jak w rysunkach 08–12; kształt znacznika to drugie kodowanie
SERIES_STYLE = [("#2a78d6", "o"), ("#eb6834", "s"), ("#1baf7a", "D")]


def e4_experiments() -> dict[str, tuple[str, str]]:
    """Nazwa eksperymentu E4 → (zestaw cech, zadanie)."""
    return {name: (exp.feature_set, exp.task) for name, exp in EXPERIMENTS.items()
            if name.startswith("e4_")}


def _read(results: Path, name: str, file: str) -> pd.DataFrame:
    path = results / name / file
    if not path.exists():
        raise FileNotFoundError(f"Brak wyników {path}; uruchom: python src/train.py "
                                f"--experiment {name}")
    return pd.read_csv(path)


def load_e4(results: Path, file: str) -> pd.DataFrame:
    return pd.concat([_read(results, name, file).assign(feature_set=fs, task=task)
                      for name, (fs, task) in e4_experiments().items()], ignore_index=True)


def n_features() -> dict[str, int]:
    return {fs: len(FEATURE_SETS[fs](feature_list())) for fs in FEATURE_SET_ORDER}


def feature_set_table(folds: pd.DataFrame) -> pd.DataFrame:
    """F1 makro po sesjach: średnia i odchylenie po foldach dla zadania × zestawu × modelu."""
    session = folds[folds["split"] == "session"]
    table = (session.groupby(["task", "feature_set", "model"])["f1_macro"]
             .agg(["mean", "std"]).reset_index())
    return table


def model_ranking(table: pd.DataFrame, task: str, feature_set: str) -> str:
    sub = table.query("task == @task and feature_set == @feature_set "
                      "and model in @TRAINED_MODELS").sort_values("mean", ascending=False)
    return " > ".join(MODEL_LABELS[m] for m in sub["model"])


def split_comparison(results: Path, folds: pd.DataFrame) -> pd.DataFrame:
    """E1 (losowy) i E2 (sesje): wszystkie cechy z 03b obok zestawu bez Idle * z E4."""
    old = pd.concat([_read(results, f"e1e2_{t}", "folds.csv").assign(feature_set="all", task=t)
                     for t in TASK_ORDER], ignore_index=True)
    new = folds[folds["feature_set"] == "bez_idle"]
    both = pd.concat([old, new], ignore_index=True)
    return (both.groupby(["task", "model", "feature_set", "split"])["f1_macro"].mean()
            .unstack(["feature_set", "split"]))


def importance_table(importance: pd.DataFrame) -> pd.DataFrame:
    """Gini i spadek F1 po permutacji grupy: średnia i odchylenie po foldach (RF, sesje)."""
    session = importance[importance["split"] == "session"]
    return (session.groupby(["task", "feature_set", "group"])
            .agg(n_features=("n_features", "first"), gini=("gini", "mean"),
                 perm=("perm_mean", "mean"), perm_std=("perm_mean", "std"))
            .reset_index())


def _pm(mean: float, std: float) -> str:
    return f"{_num(mean)} ± {_num(std)}"


def _feature_set_section(table: pd.DataFrame, task: str, counts: dict[str, int]) -> list[str]:
    lines = ["| Zestaw cech | cechy | " + " | ".join(MODEL_LABELS[m] for m in MODEL_ORDER)
             + " | ranking modeli |", "| --- | ---: |" + " ---: |" * len(MODEL_ORDER) + " --- |"]
    for fs in FEATURE_SET_ORDER:
        cells = []
        for m in MODEL_ORDER:
            r = table.query("task == @task and feature_set == @fs and model == @m").iloc[0]
            cells.append(_pm(r["mean"], r["std"]))
        lines.append(f"| {FEATURE_SET_LABELS[fs]} | {counts[fs]} | " + " | ".join(cells)
                     + f" | {model_ranking(table, task, fs)} |")
    return lines + [""]


def _split_section(splits: pd.DataFrame, task: str) -> list[str]:
    lines = ["| Model | E1 wszystkie (03b) | E2 wszystkie (03b) | E1 − E2 | "
             "E1 bez Idle * | E2 bez Idle * | E1 − E2 |", "| --- |" + " ---: |" * 6]
    for m in MODEL_ORDER:
        r = splits.loc[(task, m)]
        a1, a2 = r[("all", "random")], r[("all", "session")]
        b1, b2 = r[("bez_idle", "random")], r[("bez_idle", "session")]
        lines.append(f"| {MODEL_LABELS[m]} | {_num(a1)} | {_num(a2)} | {_num(a1 - a2)} | "
                     f"{_num(b1)} | {_num(b2)} | {_num(b1 - b2)} |")
    return lines + [""]


def _importance_section(imp: pd.DataFrame, task: str) -> list[str]:
    head = " | ".join(f"perm. {FEATURE_SET_LABELS[fs]}" for fs in IMPORTANCE_SETS)
    gini = " | ".join(f"Gini {FEATURE_SET_LABELS[fs]}" for fs in IMPORTANCE_SETS)
    lines = [f"| Grupa | cechy (wszystkie) | {head} | {gini} |",
             "| --- | ---: |" + " ---: |" * (2 * len(IMPORTANCE_SETS))]
    sub = imp[imp["task"] == task]
    order = (sub[sub["feature_set"] == "all"].sort_values("perm", ascending=False)["group"])
    for g in order:
        rows = {fs: sub.query("feature_set == @fs and group == @g") for fs in IMPORTANCE_SETS}
        perm = [_pm(r["perm"].iloc[0], r["perm_std"].iloc[0]) if len(r) else "–"
                for r in rows.values()]
        gin = [_num(r["gini"].iloc[0]) if len(r) else "–" for r in rows.values()]
        n = rows["all"]["n_features"].iloc[0]
        lines.append(f"| {GROUP_LABELS[g]} | {n} | " + " | ".join(perm + gin) + " |")
    return lines + [""]


def markdown_report(table: pd.DataFrame, splits: pd.DataFrame, imp: pd.DataFrame) -> str:
    lines = ["# Etap 04: E4, zestawy cech i ważność grup cech", "",
             "Wygenerowane przez `src/make_figures_04_e4.py` z `reports/results/e4_*` "
             "(i `e1e2_*` z 03b). Podział po sesjach, foldy jak w 03b (5, dla 3 usług 3). "
             "F1 makro: średnia ± odchylenie po foldach zewnętrznych. Zestawy poza „wszystkie” "
             "nie mają `Idle *` (przeciek daty nagrania, docs/decyzje.md). Skróty: `Idle *`, "
             "`Fwd Seg Size Min`, `FWD/Bwd Init Win Bytes`.", "",
             "Ważność grup: RF z każdego foldu, liczona na jego teście. Permutacja = spadek "
             "F1 makro, gdy wszystkie kolumny grupy dostają tę samą permutację wierszy "
             "(5 powtórzeń); Gini = suma `feature_importances_` w grupie.", ""]
    counts = n_features()
    for task in TASK_ORDER:
        lines += [f"## {TASK_LABELS[task]}", "", "### F1 makro dla zestawów cech", ""]
        lines += _feature_set_section(table, task, counts)
        lines += ["### E1/E2 z `Idle *` i bez", ""]
        lines += _split_section(splits, task)
        lines += ["### Ważność grup cech (RF)", ""]
        lines += _importance_section(imp, task)
    return "\n".join(lines)


def _style_x(ax: plt.Axes) -> None:
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v, 2)))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_MUTED)
    ax.tick_params(colors=INK_MUTED, labelcolor=INK)


def feature_set_figure(folds: pd.DataFrame) -> plt.Figure:
    """F1 makro per fold (małe znaczniki) i średnia (duże) dla zestawów cech, panel na zadanie."""
    session = folds[folds["split"] == "session"]
    fig, axes = plt.subplots(1, len(TASK_ORDER), figsize=(14, 4.8), sharey=True)
    height = 0.6 / len(TRAINED_MODELS)
    for ax, task in zip(axes, TASK_ORDER):
        for i, fs in enumerate(FEATURE_SET_ORDER):
            for j, (model, (color, marker)) in enumerate(zip(TRAINED_MODELS, SERIES_STYLE)):
                vals = session.query("task == @task and feature_set == @fs "
                                     "and model == @model")["f1_macro"]
                y = i + (j - (len(TRAINED_MODELS) - 1) / 2) * height
                ax.scatter(vals, np.full(len(vals), y), s=16, color=color, alpha=0.5,
                           marker=marker, linewidths=0)
                ax.scatter([vals.mean()], [y], s=64, color=color, marker=marker,
                           edgecolors="white", linewidths=1.5, zorder=3,
                           label=MODEL_LABELS[model] if i == 0 else None)
        ax.set_yticks(range(len(FEATURE_SET_ORDER)),
                      [FEATURE_SET_LABELS[fs] for fs in FEATURE_SET_ORDER])
        ax.invert_yaxis()
        ax.set_title(TASK_LABELS[task], fontsize=10, color=INK)
        ax.set_xlabel("F1 makro (fold zewnętrzny, podział po sesjach)", color=INK)
        _style_x(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=len(TRAINED_MODELS), frameon=False)
    fig.suptitle("E4: F1 makro dla zestawów cech (Dummy w tabeli)", x=0.01, ha="left",
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


def importance_figure(imp: pd.DataFrame) -> plt.Figure:
    """Spadek F1 po permutacji grupy (średnia ± odchylenie po foldach), RF, trzy zestawy cech."""
    fig, axes = plt.subplots(1, len(TASK_ORDER), figsize=(14, 4.4), sharey=True)
    groups = list(GROUP_LABELS)
    height = 0.75 / len(IMPORTANCE_SETS)
    for ax, task in zip(axes, TASK_ORDER):
        for j, (fs, (color, _)) in enumerate(zip(IMPORTANCE_SETS, SERIES_STYLE)):
            sub = imp.query("task == @task and feature_set == @fs").set_index("group")
            present = [g for g in groups if g in sub.index]
            y = [groups.index(g) + (j - (len(IMPORTANCE_SETS) - 1) / 2) * height
                 for g in present]
            ax.barh(y, sub.loc[present, "perm"], height=height * 0.85, color=color,
                    xerr=sub.loc[present, "perm_std"], ecolor=INK_MUTED,
                    error_kw={"linewidth": 0.8}, label=FEATURE_SET_LABELS[fs])
        ax.axvline(0, color=INK_MUTED, linewidth=0.8)
        ax.set_yticks(range(len(groups)), [GROUP_LABELS[g] for g in groups])
        ax.invert_yaxis()
        ax.set_title(TASK_LABELS[task], fontsize=10, color=INK)
        ax.set_xlabel("spadek F1 makro po permutacji grupy", color=INK)
        _style_x(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=len(IMPORTANCE_SETS), frameon=False,
               title="zestaw cech modelu", title_fontsize=9)
    fig.suptitle("E4: ważność permutacyjna grup cech, RF (Gini w tabeli)", x=0.01, ha="left",
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    return fig


def main() -> None:
    folds = load_e4(RESULTS, "folds.csv")
    importance = load_e4(RESULTS, "importance.csv")
    table, imp = feature_set_table(folds), importance_table(importance)
    out_table = RESULTS / "04_e4_tabela.md"
    out_table.write_text(markdown_report(table, split_comparison(RESULTS, folds), imp),
                         encoding="utf-8")
    folds.to_csv(RESULTS / "04_e4_folds.csv", index=False)
    importance.to_csv(RESULTS / "04_e4_importance.csv", index=False)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for fig, name in [(feature_set_figure(folds), "13_e4_zestawy_cech.png"),
                      (importance_figure(imp), "14_e4_waznosc_grup.png")]:
        fig.savefig(FIGURES / name, dpi=150)
        plt.close(fig)
    print(f"Tabela: {out_table}\nRysunki: 13_e4_zestawy_cech.png, 14_e4_waznosc_grup.png")


if __name__ == "__main__":
    sys.exit(main())
