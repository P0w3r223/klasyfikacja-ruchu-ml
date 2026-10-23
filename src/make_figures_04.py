"""Tabela i rysunek etapu 04, część E3 (wpływ VPN), z wyników w reports/results/.

    python src/make_figures_04.py

Czyta gotowe wyniki eksperymentów e3_* (wszystkie cechy, bez Idle *, bez
skrótów); nic nie trenuje i nie potrzebuje predictions.parquet. Zapisuje
reports/results/04_e3_tabela.md, 04_e3_folds.csv i rysunek 12 w reports/figures/.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from experiments import E3_TASKS, EXPERIMENTS  # noqa: E402
from make_figures_03b import (INK, MODEL_LABELS, MODEL_ORDER, _num,  # noqa: E402
                              _style_axes)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
FIGURES = ROOT / "reports" / "figures"

# trening → test; kolejność jak w E3_TASKS
E3_LABELS = dict(zip(E3_TASKS, ["zwykły → zwykły", "VPN → VPN", "zwykły → VPN", "mieszany"]))
E3_STYLE = dict(zip(E3_TASKS, [("#2a78d6", "o"), ("#eb6834", "s"),
                               ("#1baf7a", "D"), ("#eda100", "^")]))
FEATURE_SET_ORDER = ["all", "bez_idle", "bez_skrotow"]
FEATURE_SET_LABELS = {"all": "wszystkie cechy", "bez_idle": "bez Idle *",
                      "bez_skrotow": "bez skrótów (Idle *, Fwd Seg Size Min, Init Win Bytes)"}
CLASSES = ("VoIP", "Video")


def e3_experiments() -> dict[str, tuple[str, str]]:
    """Nazwa eksperymentu E3 → (zestaw cech, zadanie)."""
    return {name: (exp.feature_set, exp.task) for name, exp in EXPERIMENTS.items()
            if name.startswith("e3_")}


def load_e3_folds(results: Path) -> pd.DataFrame:
    frames = []
    for name, (feature_set, _) in e3_experiments().items():
        path = results / name / "folds.csv"
        if not path.exists():
            raise FileNotFoundError(f"Brak wyników {path}; uruchom: python src/train.py "
                                    f"--experiment {name}")
        frames.append(pd.read_csv(path).assign(feature_set=feature_set))
    return pd.concat(frames, ignore_index=True)


def e3_table(folds: pd.DataFrame) -> pd.DataFrame:
    """Średnia, odchylenie, zakres i wartości per fold F1 makro dla zestawu × wariantu × modelu."""
    rows = []
    for (feature_set, task, model), g in folds.groupby(["feature_set", "task", "model"]):
        g = g.sort_values("fold")
        rows.append({
            "feature_set": feature_set, "task": task, "model": model,
            "f1_mean": g["f1_macro"].mean(), "f1_std": g["f1_macro"].std(),
            "f1_min": g["f1_macro"].min(), "f1_max": g["f1_macro"].max(),
            "f1_folds": g["f1_macro"].tolist(),
            "f1_sw": g["f1_macro_session_weighted"].mean(),
            **{f"f1_{c}": g[f"f1_{c}"].mean() for c in CLASSES},
            **{f"f1_{c}_std": g[f"f1_{c}"].std() for c in CLASSES},
            "voip_sessions": g["n_test_sessions_VoIP"].tolist()})
    table = pd.DataFrame(rows)
    order = {"feature_set": FEATURE_SET_ORDER, "task": list(E3_TASKS), "model": MODEL_ORDER}
    for col, values in order.items():
        table[col] = pd.Categorical(table[col], values, ordered=True)
    return table.sort_values(["feature_set", "model", "task"]).reset_index(drop=True)


def markdown_table(table: pd.DataFrame) -> str:
    lines = ["# Etap 04: E3, wpływ tunelu VPN (VoIP vs Video, kampania VPN-nonVPN)", "",
             "Wygenerowane przez `src/make_figures_04.py` z `reports/results/e3_*`. "
             "Podział po sesjach, 3 foldy zewnętrzne w każdym wariancie. Warianty z testem "
             "na VPN mają te same foldy VPN; w wariancie zwykły → VPN trening to cały ruch "
             "zwykły. Wariant mieszany różni się od E2 w 03b liczbą foldów (3 zamiast 5). "
             "`Idle *` w 51% przepływów to bezwzględny czas przepływu (data nagrania), "
             "patrz docs/decyzje.md.", ""]
    for feature_set in FEATURE_SET_ORDER:
        lines += [f"## {FEATURE_SET_LABELS[feature_set]}", "",
                  "| Model | Trening → test | F1 makro | odch. | min–max | per fold | "
                  "F1 ważone sesjami | F1 VoIP (odch.) | F1 Video (odch.) | sesje VoIP w teście |",
                  "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |"]
        for r in table[table["feature_set"] == feature_set].itertuples():
            folds = " · ".join(_num(v) for v in r.f1_folds)
            sessions = " · ".join(str(v) for v in r.voip_sessions)
            lines.append(
                f"| {MODEL_LABELS[r.model]} | {E3_LABELS[r.task]} | {_num(r.f1_mean)} | "
                f"{_num(r.f1_std)} | {_num(r.f1_min)}–{_num(r.f1_max)} | {folds} | "
                f"{_num(r.f1_sw)} | {_num(r.f1_VoIP)} ({_num(r.f1_VoIP_std)}) | "
                f"{_num(r.f1_Video)} ({_num(r.f1_Video_std)}) | {sessions} |")
        lines.append("")
    return "\n".join(lines)


def e3_figure(folds: pd.DataFrame, models: list[str]) -> plt.Figure:
    """F1 makro per fold (małe znaczniki) i średnia (duże) dla wariantów E3, panel na zestaw cech."""
    fig, axes = plt.subplots(1, len(FEATURE_SET_ORDER), figsize=(14, 4.4), sharey=True)
    width = 0.7 / len(E3_TASKS)
    for ax, feature_set in zip(axes, FEATURE_SET_ORDER):
        for i, model in enumerate(models):
            for j, task in enumerate(E3_TASKS):
                vals = folds.query("feature_set == @feature_set and task == @task "
                                   "and model == @model")["f1_macro"]
                color, marker = E3_STYLE[task]
                x = i + (j - (len(E3_TASKS) - 1) / 2) * width
                ax.scatter(np.full(len(vals), x), vals, s=18, color=color, alpha=0.55,
                           marker=marker, linewidths=0)
                ax.scatter([x], [vals.mean()], s=70, color=color, marker=marker,
                           edgecolors="white", linewidths=1.5, zorder=3,
                           label=E3_LABELS[task] if i == 0 else None)
        ax.set_xticks(range(len(models)), [MODEL_LABELS[m] for m in models])
        title = FEATURE_SET_LABELS[feature_set].split(" (")[0]
        ax.set_title(title, fontsize=10, color=INK)
        _style_axes(ax)
    axes[0].set_ylabel("F1 makro (fold zewnętrzny)", color=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=len(E3_TASKS), frameon=False,
               title="trening → test", title_fontsize=9)
    fig.suptitle("E3: VoIP vs Video w ruchu zwykłym i VPN (3 foldy po sesjach; Dummy w tabeli)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    return fig


def main() -> None:
    folds = load_e3_folds(RESULTS)
    out_table = RESULTS / "04_e3_tabela.md"
    out_table.write_text(markdown_table(e3_table(folds)), encoding="utf-8")
    folds.to_csv(RESULTS / "04_e3_folds.csv", index=False)
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig = e3_figure(folds, [m for m in MODEL_ORDER if m != "dummy"])
    fig.savefig(FIGURES / "12_e3_warianty.png", dpi=150)
    plt.close(fig)
    print(f"Tabela: {out_table}\nRysunek: 12_e3_warianty.png")


if __name__ == "__main__":
    sys.exit(main())
