"""Rysunki etapu 08: do raportu (16: E5, 17: E7) i do slajdów (S1–S5, 16:9, czytelne z daleka).

Dane przychodzą z `wyniki_dane.py`; tu tylko rysowanie. Slajdy pokazują jeden przekaz na
rysunek: RF i poziom zgadywania (Dummy / klasa większości), bez punktów foldów.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from make_figures_03b import GRID, INK, INK_MUTED, MODEL_LABELS, _num, _style_axes  # noqa: E402
from wyniki_dane import (STEP_CLEAN, STEP_EXTERNAL, STEPS, TASK_SHORT, TASKS,  # noqa: E402
                         TRAINED)

# barwy w stałej kolejności jak w rysunkach 08–15 (paleta sprawdzona walidatorem CVD)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
MARKERS = ["o", "s", "D", "^"]
TASK_STYLE = dict(zip(TASKS, zip(SERIES, MARKERS)))
MODEL_STYLE = dict(zip(TRAINED, zip(SERIES, MARKERS)))
SERVICE_COLORS = dict(zip(["WWW", "VoIP", "Video"], SERIES))
CHANCE = "#8d8c87"
SLIDE_SIZE = (13.33, 7.5)
SLIDE_RC = {"font.size": 20, "axes.titlesize": 24, "axes.labelsize": 20,
            "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 18}
FEATURE_SET_SHORT = {"all": "wszystkie cechy", "bez_idle": "bez Idle *",
                     "bez_skrotow": "bez skrótów", "tylko_rozmiarowe": "tylko rozmiarowe",
                     "tylko_czasowe": "tylko czasowe", "czasowe_tempo": "czasowe + tempo",
                     "bez_protocol": "bez Idle * i Protocol"}
# etykiety wartości na S1: VoIP nad punktem, WWW pod, 3 usługi z prawej (linie są blisko siebie)
STORY_LABEL_OFFSET = {"voip_video_vpncamp": ((0, 18), "center"),
                      "www_video_tor": ((0, -20), "center"),
                      "uslugi3_plain": ((14, 0), "left")}
# tam, gdzie domyślna pozycja nachodzi na inny punkt albo na nazwę serii
STORY_LABEL_OVERRIDE = {("www_video_tor", STEP_CLEAN): ((0, 20), "center"),
                        ("uslugi3_plain", STEP_EXTERNAL): ((-16, 0), "right")}
E5_ROWS = [("tor-nontor", "plain", "Tor-nonTor, zwykły"),
           ("vpn-nonvpn", "plain", "VPN-nonVPN, zwykły"),
           ("vpn-nonvpn", "vpn", "VPN-nonVPN, VPN")]


def _slide(title: str) -> tuple[plt.Figure, plt.Axes]:
    with plt.rc_context(SLIDE_RC):
        fig, ax = plt.subplots(figsize=SLIDE_SIZE)
    fig.suptitle(title, x=0.02, ha="left", fontsize=26, color=INK)
    return fig, ax


def _slide_axes(ax: plt.Axes, axis: str = "y") -> None:
    _style_axes(ax)
    ax.tick_params(labelsize=18)
    if axis == "x":
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID, linewidth=0.8)


def _chance_line(ax: plt.Axes, y: float, label: str, horizontal: bool = True) -> None:
    draw = ax.axhline if horizontal else ax.axvline
    draw(y, color=CHANCE, linewidth=2, linestyle=(0, (4, 3)), zorder=1)
    if horizontal:
        ax.text(ax.get_xlim()[1], y, f" {label}", va="center", ha="left", fontsize=16,
                color=INK_MUTED)


def story_slide(steps: pd.DataFrame) -> plt.Figure:
    """S1: F1 makro RF na kolejnych krokach; podpis serii przy ostatnim punkcie."""
    fig, ax = _slide("Ile zostaje z wysokiego wyniku? F1 makro, Random Forest")
    x = np.arange(len(STEPS))
    for task in TASKS:
        rf = steps.query("task == @task and model == 'rf'").set_index("step").loc[STEPS]
        color, marker = TASK_STYLE[task]
        ax.plot(x, rf["mean"], color=color, marker=marker, markersize=13, linewidth=3,
                markeredgecolor="white", markeredgewidth=2)
        for xi, step, v in zip(x, STEPS, rf["mean"]):
            offset, ha = STORY_LABEL_OVERRIDE.get((task, step), STORY_LABEL_OFFSET[task])
            ax.annotate(_num(v, 2), (xi, v), textcoords="offset points", xytext=offset,
                        ha=ha, va="center", fontsize=16, color=INK)
        ax.annotate(TASK_SHORT[task], (x[-1], rf["mean"].iloc[-1]), textcoords="offset points",
                    xytext=(22, 0), va="center", fontsize=18, color=INK)
    ax.axvspan(2.5, 3.5, color=GRID, alpha=0.6, zorder=0)
    ax.set_xticks(x, ["podział\nlosowy (E1)", "podział po\nsesjach (E2)",
                      "E2 bez skrótów\n(przecieku)", "inny zbiór\n(USBVPN2022)"])
    ax.set_xlim(-0.4, 3.4)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("F1 makro")
    _slide_axes(ax)
    ax.text(0.0, -0.2, "Zgadywanie: F1 ≈ 0,5 (2 klasy), ≈ 0,33 (3 usługi).\n"
            "Kroki 1–3: walidacja krzyżowa na CIC-Darknet2020; krok 4: tylko test.",
            transform=ax.transAxes, va="top", fontsize=15, color=INK_MUTED)
    fig.subplots_adjust(left=0.08, right=0.84, top=0.86, bottom=0.24)
    return fig


def campaign_slide(test: pd.DataFrame) -> plt.Figure:
    """S2: kampanię pomiarową rozpoznaje się z samego wideo, także bez skrótów."""
    fig, ax = _slide("Kampanię pomiarową widać w samym wideo")
    order = ["all", "bez_skrotow", "tylko_rozmiarowe", "tylko_czasowe"]
    rows = test.set_index("feature_set").loc[order]
    _slide_axes(ax, axis="x")
    y = np.arange(len(order))[::-1]
    ax.barh(y, rows["mean"], xerr=rows["std"], color=SERIES[0], height=0.6, edgecolor="white",
            error_kw={"ecolor": INK_MUTED, "elinewidth": 2, "capsize": 0})
    for yi, v, s in zip(y, rows["mean"], rows["std"]):
        ax.text(v + s + 0.015, yi, _num(v), va="center", ha="left", fontsize=18, color=INK)
    ax.set_yticks(y, [FEATURE_SET_SHORT[f] for f in order])
    ax.set_xlim(0, 1.13)
    ax.set_xticks(np.linspace(0, 1, 6), [_num(v, 1) for v in np.linspace(0, 1, 6)])
    ax.axvline(0.5, color=CHANCE, linewidth=2, linestyle=(0, (4, 3)))
    ax.text(0.5, len(order) - 0.45, "zgadywanie", ha="center", va="bottom", fontsize=16,
            color=INK_MUTED)
    ax.set_xlabel("dokładność zbalansowana rozpoznania kampanii (RF, po sesjach)")
    fig.subplots_adjust(left=0.24, right=0.96, top=0.84, bottom=0.16)
    return fig


def e3_slide(e3: pd.DataFrame) -> plt.Figure:
    """S3: pozorny spadek przy przenoszeniu modelu na VPN znika po usunięciu Idle *."""
    fig, ax = _slide("VPN: spadek był przeciekiem daty, nie efektem tunelu")
    sets = ["all", "bez_idle", "bez_skrotow"]
    variants = [("voip_video_vpn", "VPN → VPN"), ("voip_video_plain2vpn", "zwykły → VPN")]
    rf = e3.query("model == 'rf'").set_index(["feature_set", "task"])
    width = 0.36
    for j, (task, label) in enumerate(variants):
        x = np.arange(len(sets)) + (j - 0.5) * width
        vals = [rf.loc[(s, task), "mean"] for s in sets]
        ax.bar(x, vals, width=width - 0.03, color=SERIES[j], label=label, edgecolor="white")
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.02, _num(v, 2), ha="center", fontsize=18, color=INK)
    ax.set_xticks(range(len(sets)), [FEATURE_SET_SHORT[s] for s in sets])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("F1 makro, VoIP vs Video (RF)")
    _slide_axes(ax)
    _chance_line(ax, 0.5, "zgadywanie")
    ax.legend(title="trening → test", loc="upper left", bbox_to_anchor=(1.0, 0.98),
              frameon=False, fontsize=18, title_fontsize=18)
    fig.subplots_adjust(left=0.09, right=0.76, top=0.86, bottom=0.12)
    return fig


def e6_slide(curve: pd.DataFrame, full_flow: int = 0) -> plt.Figure:
    """S4: F1 makro RF od liczby pierwszych pakietów (populacja: wszystkie przepływy)."""
    fig, ax = _slide("Wystarczy 5 pierwszych pakietów (VoIP vs Video)")
    rf = curve.query("population == 'wszystkie' and model == 'rf'")
    prefix = rf[rf["n_first"] != full_flow].sort_values("n_first")
    full = rf[rf["n_first"] == full_flow].iloc[0]
    labels = [str(n) for n in prefix["n_first"]] + ["pełny\nprzepływ"]
    means = [*prefix["f1_macro_mean"], full["f1_macro_mean"]]
    stds = [*prefix["f1_macro_std"], full["f1_macro_std"]]
    x = np.arange(len(labels))
    ax.errorbar(x, means, yerr=stds, color=SERIES[2], marker="D", markersize=14, linewidth=3,
                elinewidth=2, ecolor=INK_MUTED, markeredgecolor="white", markeredgewidth=2)
    for xi, v in zip(x, means):
        ax.annotate(_num(v), (xi, v), textcoords="offset points", xytext=(18, 8),
                    fontsize=18, color=INK)
    ax.set_xticks(x, labels)
    ax.set_xlabel("liczba pierwszych pakietów przepływu (N)")
    ax.set_ylabel("F1 makro (RF, po sesjach)")
    ax.set_ylim(0.4, 1.05)
    _slide_axes(ax)
    dummy = curve.query("population == 'wszystkie' and model == 'dummy'")["f1_macro_mean"]
    _chance_line(ax, float(dummy.mean()), "Dummy")
    ax.text(0.0, -0.26, "Pionowe kreski: odchylenie między 5 foldami. Różnice N − pełny mieszczą "
            "się w rozrzucie foldów:\nbrak wykrytej różnicy, nie dowód równoważności.",
            transform=ax.transAxes, va="top", fontsize=15, color=INK_MUTED)
    fig.subplots_adjust(left=0.09, right=0.88, top=0.86, bottom=0.27)
    return fig


def e7_slide(e7: pd.DataFrame) -> plt.Figure:
    """S5: RF, walidacja krzyżowa na Darknet vs test na USBVPN2022."""
    fig, ax = _slide("Inny zbiór: modele spadają do poziomu zgadywania")
    rf = e7.query("model == 'rf'").set_index("task").loc[TASKS]
    width = 0.36
    x = np.arange(len(TASKS))
    for j, (col, label) in enumerate([("cv_f1_macro", "CIC-Darknet2020:\nCV po sesjach"),
                                      ("f1_macro", "USBVPN2022:\ntylko test")]):
        xs = x + (j - 0.5) * width
        ax.bar(xs, rf[col], width=width - 0.03, color=SERIES[j], label=label, edgecolor="white")
        for xi, v in zip(xs, rf[col]):
            ax.text(xi, v + 0.02, _num(v, 2), ha="center", fontsize=18, color=INK)
    for xi, v in zip(x, rf["f1_macro_majority"]):
        ax.plot([xi - width, xi + width], [v, v], color=CHANCE, linewidth=3,
                linestyle=(0, (4, 3)))
    ax.plot([], [], color=CHANCE, linewidth=3, linestyle=(0, (4, 3)),
            label="klasa większości\n(USBVPN2022)")
    ax.set_xticks(x, [TASK_SHORT[t] for t in TASKS])
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("F1 makro (RF)")
    _slide_axes(ax)
    handles, labels = ax.get_legend_handles_labels()
    # matplotlib wstawia linie przed słupkami; w legendzie słupki idą pierwsze
    ax.legend(handles[1:] + handles[:1], labels[1:] + labels[:1], loc="upper left",
              bbox_to_anchor=(1.0, 0.98), frameon=False, fontsize=17, labelspacing=1.0)
    fig.subplots_adjust(left=0.09, right=0.72, top=0.86, bottom=0.12)
    return fig


def e5_figure(shares: pd.DataFrame) -> plt.Figure:
    """Rysunek 16: do jakich klas potoki 3-klasowe przypisują przepływy Audio (E5)."""
    fig, axes = plt.subplots(1, len(TRAINED), figsize=(13, 3.8), sharey=True)
    y = np.arange(len(E5_ROWS))[::-1]
    for ax, model in zip(axes, TRAINED):
        rows = shares[shares["model"] == model].set_index(["campaign", "tunnel"])
        left = np.zeros(len(E5_ROWS))
        for service, color in SERVICE_COLORS.items():
            vals = np.array([rows.loc[(c, t), f"share_{service}"] for c, t, _ in E5_ROWS])
            ax.barh(y, vals, left=left, color=color, height=0.62, edgecolor="white",
                    linewidth=2, label=service if model == TRAINED[0] else None)
            for yi, lo, v in zip(y, left, vals):
                if v >= 0.12:
                    ax.text(lo + v / 2, yi, f"{100 * v:.0f}%", ha="center", va="center",
                            fontsize=10, color="white", fontweight="bold")
            left += vals
        ax.set_title(MODEL_LABELS[model], fontsize=11, color=INK)
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.5, 1], ["0%", "50%", "100%"])
        _style_axes(ax)
        ax.grid(axis="y", visible=False)
    totals = shares[shares["model"] == TRAINED[0]].set_index(["campaign", "tunnel"])["total"]
    axes[0].set_yticks(y, [f"{label} ({totals.loc[(c, t)]})" for c, t, label in E5_ROWS])
    fig.legend(loc="upper right", ncol=3, frameon=False, title="przewidziana klasa")
    fig.suptitle("E5: przepływy Audio przez potoki 3 usług (odsetek przepływów)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    return fig


def e7_figure(e7: pd.DataFrame) -> plt.Figure:
    """Rysunek 17: F1 makro, CV na Darknet (± odchylenie) vs test na USBVPN2022, 9 potoków."""
    fig, axes = plt.subplots(1, len(TASKS), figsize=(13, 4.2), sharey=True)
    width = 0.36
    for ax, task in zip(axes, TASKS):
        rows = e7[e7["task"] == task].set_index("model").loc[TRAINED]
        x = np.arange(len(TRAINED))
        ax.bar(x - width / 2, rows["cv_f1_macro"], width - 0.03, yerr=rows["cv_f1_macro_std"],
               color=SERIES[0], label="CIC-Darknet2020, CV po sesjach",
               error_kw={"ecolor": INK_MUTED})
        ax.bar(x + width / 2, rows["f1_macro"], width - 0.03, color=SERIES[1],
               label="USBVPN2022, test")
        majority = float(rows["f1_macro_majority"].iloc[0])
        ax.axhline(majority, color=CHANCE, linewidth=1.5, linestyle=(0, (4, 3)),
                   label="klasa większości (USBVPN2022)")
        ax.set_xticks(x, [MODEL_LABELS[m] for m in TRAINED])
        ax.set_title(TASK_SHORT[task], fontsize=10, color=INK)
        ax.set_ylim(0, 1.05)
        _style_axes(ax)
    axes[0].set_ylabel("F1 makro", color=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(1.0, 0.92), ncol=3,
               frameon=False)
    fig.suptitle("E7: modele z CIC-Darknet2020 na zbiorze USBVPN2022 (bez treningu)",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    return fig
