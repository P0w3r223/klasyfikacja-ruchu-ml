"""Tabela i rysunki etapu 03b (E1/E2) z wyników w reports/results/.

    python src/make_figures_03b.py

Czyta gotowe wyniki eksperymentów e1e2_*, e2_gap15_*, e2_ippair_*; nic nie
trenuje. Sekcja o efekcie kampanii potrzebuje lokalnych predictions.parquet
(poza gitem) i flows.parquet, więc całość odtwarza się na maszynie, która
liczyła eksperymenty. Zapisuje reports/results/03b_tabela.md, 03b_folds.csv
i rysunki 08–11 w reports/figures/.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from experiments import EXPERIMENTS, TASKS, Experiment  # noqa: E402
from features import load_flows  # noqa: E402
from train import task_frame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
FIGURES = ROOT / "reports" / "figures"
PREFIXES = ("e1e2_", "e2_gap15_", "e2_ippair_")

# zadania wewnątrz kampanii są główną miarą, 3 usługi to punkt odniesienia
TASK_ORDER = ["www_video_tor", "voip_video_vpncamp", "uslugi3_plain"]
TASK_LABELS = {"www_video_tor": "WWW vs Video (Tor-nonTor)",
               "voip_video_vpncamp": "VoIP vs Video (VPN-nonVPN)",
               "uslugi3_plain": "3 usługi, ruch zwykły (odniesienie)"}
MODEL_ORDER = ["dummy", "knn", "tree", "rf"]
MODEL_LABELS = {"dummy": "Dummy", "knn": "k-NN", "tree": "drzewo", "rf": "RF"}

E1, E2, E2_15, E2_PAIR = "E1 losowy", "E2 sesje 5 min", "E2 sesje 15 min", "E2 para IP"
VARIANT_ORDER = [E1, E2, E2_15, E2_PAIR]
# kolejność barw stała we wszystkich rysunkach; kształt znacznika to drugie kodowanie
VARIANT_STYLE = {E1: ("#2a78d6", "o"), E2: ("#eb6834", "s"),
                 E2_15: ("#1baf7a", "D"), E2_PAIR: ("#eda100", "^")}
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def variant(exp: Experiment, split: str) -> str:
    if split == "random":
        return E1
    if exp.group_by == "ip_pair":
        return E2_PAIR
    return E2_15 if exp.session_gap_min == 15.0 else E2


def load_folds(results: Path) -> pd.DataFrame:
    """Wyniki per fold ze wszystkich eksperymentów 03b, z kolumną variant."""
    frames = []
    for name, exp in EXPERIMENTS.items():
        if not name.startswith(PREFIXES):
            continue
        path = results / name / "folds.csv"
        if not path.exists():
            raise FileNotFoundError(f"Brak wyników {path}; uruchom: python src/train.py "
                                    f"--experiment {name}")
        folds = pd.read_csv(path)
        frames.append(folds.assign(variant=[variant(exp, s) for s in folds["split"]]))
    folds = pd.concat(frames, ignore_index=True)
    test_cols = [c for c in folds.columns if c.startswith("n_test_flows_")]
    n_test = folds[test_cols].sum(axis=1)
    return folds.assign(predict_us_per_flow=folds["predict_s"] / n_test * 1e6)


def load_confusions(results: Path, task: str) -> dict[str, dict]:
    return json.loads((results / f"e1e2_{task}" / "confusion.json").read_text(encoding="utf-8"))


def summary_table(folds: pd.DataFrame) -> pd.DataFrame:
    """Średnia, odchylenie, zakres i wartości per fold F1 makro dla każdego wariantu."""
    rows = []
    for (task, model, var), g in folds.groupby(["task", "model", "variant"]):
        classes = TASKS[task].classes
        f1 = g.sort_values("fold")["f1_macro"]
        rows.append({
            "task": task, "model": model, "variant": var,
            "f1_mean": f1.mean(), "f1_std": f1.std(), "f1_min": f1.min(), "f1_max": f1.max(),
            "f1_folds": f1.tolist(), "n_folds": len(f1), "accuracy": g["accuracy"].mean(),
            **{f"f1_{c}": g[f"f1_{c}"].mean() for c in classes},
            "search_s": g["search_s"].mean(), "fit_s": g["fit_s"].mean(),
            "predict_us_per_flow": g["predict_us_per_flow"].mean()})
    table = pd.DataFrame(rows)
    order = {"task": TASK_ORDER, "model": MODEL_ORDER, "variant": VARIANT_ORDER}
    for col, values in order.items():
        table[col] = pd.Categorical(table[col], values, ordered=True)
    return table.sort_values(["task", "model", "variant"]).reset_index(drop=True)


def e1_minus_e2(table: pd.DataFrame) -> pd.DataFrame:
    """Zawyżenie wyniku przez podział losowy: różnica średnich i orientacyjny błąd std.

    Błąd liczony jak dla niezależnych prób; foldy nie są niezależne (wspólny trening)
    ani sparowane między E1 i E2, więc to tylko skala rozrzutu, nie test istotności.
    """
    wide = table.pivot(index=["task", "model"], columns="variant",
                       values=["f1_mean", "f1_std", "n_folds"])
    gap = wide[("f1_mean", E1)] - wide[("f1_mean", E2)]
    se = np.sqrt(wide[("f1_std", E1)] ** 2 / wide[("n_folds", E1)]
                 + wide[("f1_std", E2)] ** 2 / wide[("n_folds", E2)])
    return pd.DataFrame({"gap": gap, "se": se}).reset_index()


def video_recall_by_campaign(predictions: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """Czułość Video osobno dla każdej kampanii; population w kolejności wierszy z prepare()."""
    video = predictions[predictions["y_true"] == "Video"]
    video = video.assign(campaign=population["campaign"].to_numpy()[video["row"]],
                         hit=video["y_pred"] == "Video")
    return (video.groupby(["model", "split", "campaign"])["hit"].mean()
            .unstack("campaign").reset_index())


def campaign_markdown(recall: pd.DataFrame) -> str:
    campaigns = [c for c in recall.columns if c not in ("model", "split")]
    lines = ["## Wkład efektu kampanii w zadaniu 3 usług", "",
             "Czułość Video (odsetek przepływów Video rozpoznanych jako Video) "
             "osobno dla Video z każdej kampanii; WWW jest tylko w Tor-nonTor.", "",
             "| Model | Podział | " + " | ".join(f"Video {c}" for c in campaigns) + " |",
             "| --- | --- |" + " ---: |" * len(campaigns)]
    ordered = recall.sort_values(["model", "split"], key=lambda s: s.map(
        {m: i for i, m in enumerate(MODEL_ORDER)}) if s.name == "model" else s)
    for r in ordered.to_dict("records"):
        lines.append(f"| {MODEL_LABELS[r['model']]} | {E1 if r['split'] == 'random' else E2} | "
                     + " | ".join(_num(r[c]) for c in campaigns) + " |")
    return "\n".join(lines + [""])


def load_campaign_recall(results: Path, flows: pd.DataFrame) -> pd.DataFrame:
    """Wymaga lokalnych predictions.parquet (poza gitem) i flows.parquet (Release)."""
    task = "uslugi3_plain"
    predictions = pd.read_parquet(results / f"e1e2_{task}" / "predictions.parquet")
    population, _, _ = task_frame(flows, TASKS[task])
    at_rows = population.iloc[predictions["row"]]
    # zgodność usług i sesji wiersz po wierszu: przetasowanie w obrębie klasy też wyjdzie
    if not ((at_rows["service"].to_numpy() == predictions["y_true"].to_numpy()).all()
            and (at_rows["session"].to_numpy() == predictions["session"].to_numpy()).all()):
        raise ValueError("Wiersze predykcji nie pasują do populacji zadania; "
                         "flows.parquet zmienił się od przebiegu?")
    return video_recall_by_campaign(predictions, population)


def _num(x: float, digits: int = 3) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def markdown_table(table: pd.DataFrame) -> str:
    lines = ["# Etap 03b: E1 (podział losowy) vs E2 (podział po sesjach)", "",
             "Wygenerowane przez `src/make_figures_03b.py` z `reports/results/`. "
             "F1 makro: średnia, odchylenie i zakres z foldów zewnętrznych (5, dla 3 usług 3); "
             "czasy to średnie na fold (strojenie = cała siatka z CV wewnętrzną).", ""]
    for task in TASK_ORDER:
        classes = TASKS[task].classes
        sub = table[table["task"] == task]
        lines += [f"## {TASK_LABELS[task]}", "",
                  "| Model | Wariant | F1 makro | odch. | min–max | per fold |",
                  "| --- | --- | ---: | ---: | --- | --- |"]
        for r in sub.itertuples():
            folds = " · ".join(_num(v) for v in r.f1_folds)
            lines.append(f"| {MODEL_LABELS[r.model]} | {r.variant} | {_num(r.f1_mean)} | "
                         f"{_num(r.f1_std)} | {_num(r.f1_min)}–{_num(r.f1_max)} | {folds} |")
        lines += ["", "| Model | Wariant | " + " | ".join(f"F1 {c}" for c in classes)
                  + " | accuracy | strojenie [s] | refit [s] | predykcja [µs/przepływ] |",
                  "| --- | --- |" + " ---: |" * (len(classes) + 4)]
        for r in sub.itertuples():
            per_class = " | ".join(_num(getattr(r, f"f1_{c}")) for c in classes)
            lines.append(f"| {MODEL_LABELS[r.model]} | {r.variant} | {per_class} | "
                         f"{_num(r.accuracy)} | {_num(r.search_s, 1)} | {_num(r.fit_s, 2)} | "
                         f"{_num(r.predict_us_per_flow, 1)} |")
        lines.append("")
    return "\n".join(lines)


def _style_axes(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v, 2)))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_MUTED)
    ax.tick_params(colors=INK_MUTED, labelcolor=INK)


def dot_panels(folds: pd.DataFrame, variants: list[str], models: list[str],
               title: str) -> plt.Figure:
    """Kropki per fold i średnia (większy znacznik z obwódką) dla każdego wariantu."""
    fig, axes = plt.subplots(1, len(TASK_ORDER), figsize=(13, 4.2), sharey=True)
    width = 0.7 / len(variants)
    in_legend: set[str] = set()
    for ax, task in zip(axes, TASK_ORDER):
        for i, model in enumerate(models):
            for j, var in enumerate(variants):
                vals = folds.query("task == @task and model == @model and variant == @var")
                if vals.empty:
                    continue
                color, marker = VARIANT_STYLE[var]
                x = i + (j - (len(variants) - 1) / 2) * width
                ax.scatter(np.full(len(vals), x), vals["f1_macro"], s=18, color=color,
                           alpha=0.55, marker=marker, linewidths=0)
                ax.scatter([x], [vals["f1_macro"].mean()], s=70, color=color, marker=marker,
                           edgecolors="white", linewidths=1.5, zorder=3,
                           label=None if var in in_legend else var)
                in_legend.add(var)
        ax.set_xticks(range(len(models)), [MODEL_LABELS[m] for m in models])
        ax.set_title(TASK_LABELS[task], fontsize=10, color=INK)
        _style_axes(ax)
    axes[0].set_ylabel("F1 makro (fold zewnętrzny)", color=INK)
    handles, labels = zip(*[hl for ax in axes for hl in zip(*ax.get_legend_handles_labels())])
    fig.legend(handles, labels, loc="upper right", ncol=len(variants), frameon=False)
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def gap_figure(gaps: pd.DataFrame) -> plt.Figure:
    """Zawyżenie F1 makro przez podział losowy (E1 − E2) per model i zadanie."""
    fig, ax = plt.subplots(figsize=(8, 4))
    task_colors = dict(zip(TASK_ORDER, ["#2a78d6", "#eb6834", "#1baf7a"]))
    width = 0.26
    for j, task in enumerate(TASK_ORDER):
        sub = gaps[gaps["task"] == task].set_index("model").reindex(MODEL_ORDER)
        x = np.arange(len(MODEL_ORDER)) + (j - 1) * width
        ax.bar(x, sub["gap"], width * 0.92, yerr=sub["se"], color=task_colors[task],
               label=TASK_LABELS[task], error_kw={"ecolor": INK_MUTED, "lw": 1, "capsize": 3})
    ax.axhline(0, color=INK_MUTED, linewidth=1)
    ax.set_xticks(range(len(MODEL_ORDER)), [MODEL_LABELS[m] for m in MODEL_ORDER])
    ax.set_ylabel("F1 makro: E1 − E2 (±1 błąd std., orientacyjnie)", color=INK)
    _style_axes(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Zawyżenie wyniku przez podział losowy", loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    return fig


def confusion_figure(confusions: dict[str, dict[str, dict]], model: str) -> plt.Figure:
    """Macierze pomyłek (wiersz = klasa prawdziwa, % wiersza) dla E1 i E2."""
    fig, axes = plt.subplots(2, len(TASK_ORDER), figsize=(12, 7.5))
    for col, task in enumerate(TASK_ORDER):
        for row, (split, label) in enumerate([("random", E1), ("session", E2)]):
            entry = confusions[task][f"{model}/{split}"]
            counts = np.array(entry["total"])
            share = counts / counts.sum(axis=1, keepdims=True)
            ax = axes[row, col]
            ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
            for (i, k), v in np.ndenumerate(share):
                ax.text(k, i, f"{_num(100 * v, 1)}%\n({counts[i, k]})", ha="center",
                        va="center", fontsize=8, color="white" if v > 0.6 else INK)
            classes = entry["classes"]
            ax.set_xticks(range(len(classes)), classes, fontsize=8)
            ax.set_yticks(range(len(classes)), classes, fontsize=8)
            ax.set_title(f"{TASK_LABELS[task]}\n{label}", fontsize=9, color=INK)
            if col == 0:
                ax.set_ylabel("klasa prawdziwa")
            if row == 1:
                ax.set_xlabel("klasa przewidziana")
    fig.suptitle(f"Macierze pomyłek {MODEL_LABELS[model]}, suma z foldów zewnętrznych",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout()
    return fig


def main() -> None:
    folds = load_folds(RESULTS)
    table = summary_table(folds)
    out_table = RESULTS / "03b_tabela.md"
    recall = load_campaign_recall(RESULTS, load_flows())
    out_table.write_text(markdown_table(table) + "\n" + campaign_markdown(recall),
                         encoding="utf-8")
    folds.to_csv(RESULTS / "03b_folds.csv", index=False)
    trained = [m for m in MODEL_ORDER if m != "dummy"]
    figures = {
        "08_e1_vs_e2.png": dot_panels(folds, [E1, E2], trained,
                                      "F1 makro: podział losowy (E1) vs po sesjach (E2); "
                                      "Dummy w tabeli"),
        "09_zawyzenie_e1_e2.png": gap_figure(e1_minus_e2(table)),
        "10_wrazliwosc_e2.png": dot_panels(folds, [E2, E2_15, E2_PAIR], trained,
                                           "Wrażliwość E2: próg sesji 5 vs 15 min "
                                           "i grupowanie po parze IP (tylko RF)"),
        "11_macierze_rf.png": confusion_figure(
            {t: load_confusions(RESULTS, t) for t in TASK_ORDER}, "rf"),
    }
    FIGURES.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        fig.savefig(FIGURES / name, dpi=150)
        plt.close(fig)
    print(f"Tabela: {out_table}\nRysunki: {', '.join(figures)}")


if __name__ == "__main__":
    sys.exit(main())
