"""Tabele etapu 08 (reports/wyniki_tabele.md) z podsumowań `wyniki_dane.py`.

Każda sekcja podaje plik źródłowy w reports/results/. Liczby w reports/wyniki.md
pochodzą z tych tabel (test: tests/test_wyniki.py).
"""
import pandas as pd

from make_figures_03b import MODEL_LABELS, _num
from make_figures_04 import paired_vpn_difference
from wyniki_dane import (MODELS, SOURCES, TASK_SHORT, TASKS, TRAINED, campaign_test,
                         e3_summary, e4_importance, e4_summary, e5_shares, e6_curve, e6_paired,
                         e7_compare, main_table)

E3_VARIANTS = [("voip_video_plain", "zwykły → zwykły"), ("voip_video_vpn", "VPN → VPN"),
               ("voip_video_plain2vpn", "zwykły → VPN"), ("voip_video_vpncamp", "mieszany")]
FEATURE_SET_LABELS = {"all": "wszystkie", "bez_idle": "bez Idle *", "bez_skrotow": "bez skrótów",
                      "bez_protocol": "bez Idle * i Protocol", "tylko_czasowe": "tylko czasowe",
                      "czasowe_tempo": "czasowe + tempo", "tylko_rozmiarowe": "tylko rozmiarowe"}
E6_POPULATIONS = ["wszystkie", "min20"]
E6_N_ORDER = [5, 10, 20, 50, 0]
GROUP_LABELS = {"czasowe": "czasowe", "rozmiarowe": "rozmiarowe", "tempo": "tempo",
                "licznosci": "liczności", "tcp_protokol": "TCP i protokół",
                "przeciek_czasu": "Idle * (przeciek)"}


def _ordered(df: pd.DataFrame, **orders: list) -> pd.DataFrame:
    """Wiersze w stałej kolejności kategorii (modele, populacje, N), nie alfabetycznie."""
    keys = {col: df[col].map({v: i for i, v in enumerate(order)}) for col, order in orders.items()}
    return df.assign(**{f"_k_{c}": k for c, k in keys.items()}).sort_values(
        [f"_k_{c}" for c in orders]).drop(columns=[f"_k_{c}" for c in orders])


def _pm(mean: float, std: float) -> str:
    return _num(mean) if pd.isna(std) else f"{_num(mean)} ± {_num(std)}"


def _signed(x: float) -> str:
    return ("+" if x >= 0 else "−") + _num(abs(x))


def _rows(header: list[str], rows: list[list[str]], numeric_from: int = 1) -> list[str]:
    align = ["---"] * numeric_from + ["---:"] * (len(header) - numeric_from)
    return ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |",
            *["| " + " | ".join(r) + " |" for r in rows], ""]


def _section(number: str, title: str, source_keys: list[str], note: str = "") -> list[str]:
    sources = ", ".join(f"`reports/results/{SOURCES[k]}`" for k in source_keys)
    return [f"## {number}. {title}", "", f"Źródło: {sources}." + (f" {note}" if note else ""), ""]


def main_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    t = main_table(inputs).set_index(["task", "model", "variant"])["mean"]
    rows = []
    for task in TASKS:
        for model in MODELS:
            v = {var: t.get((task, model, var)) for var in
                 ["E1 wszystkie", "E2 wszystkie", "E1 bez_idle", "E2 bez_idle", "E2 bez_skrotow"]}
            rows.append([TASK_SHORT[task], MODEL_LABELS[model], _num(v["E1 wszystkie"]),
                         _num(v["E2 wszystkie"]), _signed(v["E1 wszystkie"] - v["E2 wszystkie"]),
                         _num(v["E1 bez_idle"]), _num(v["E2 bez_idle"]),
                         _signed(v["E1 bez_idle"] - v["E2 bez_idle"]), _num(v["E2 bez_skrotow"]),
                         _signed(v["E2 bez_skrotow"] - v["E2 wszystkie"])])
    header = ["Zadanie", "Model", "E1 wszystkie", "E2 wszystkie", "E1−E2", "E1 bez Idle",
              "E2 bez Idle", "E1−E2 bez Idle", "E2 bez skrótów", "bez skrótów − wszystkie"]
    return (_section("T1", "Tabela główna: F1 makro, zadanie × model × podział", ["e1e2", "e4"],
                     "Średnia z foldów zewnętrznych; E2 = sesje 5 min; 3 usługi na 3 foldach.")
            + _rows(header, rows, numeric_from=2))


def campaign_section(inputs: dict[str, pd.DataFrame],
                     video_recall: dict[str, pd.DataFrame]) -> list[str]:
    test = campaign_test(inputs)
    lines = _section("T2", "Efekt kampanii", ["kampania"],
                     "Wideo z ruchu zwykłego, cel = kampania, RF, 5 foldów po sesjach.")
    lines += _rows(["Zestaw cech", "Cech", "Dokładność zbalansowana"],
                   [[FEATURE_SET_LABELS[r.feature_set], str(r.n_features), _pm(r.mean, r.std)]
                    for r in test.itertuples()])
    lines += ["Czułość Video w zadaniu 3 usług osobno dla Video z każdej kampanii (WWW jest "
              "tylko w Tor-nonTor). Źródło: `predictions.parquet` eksperymentu (lokalnie, "
              "poza gitem) i `flows.parquet`.", ""]
    rows = []
    for experiment, recall in video_recall.items():
        for r in _ordered(recall, model=MODELS, split=["random", "session"]).to_dict("records"):
            split = "E1" if r["split"] == "random" else "E2"
            rows.append([f"`{experiment}`", MODEL_LABELS[r["model"]], split,
                         _num(r["tor-nontor"]), _num(r["vpn-nonvpn"])])
    return lines + _rows(["Eksperyment", "Model", "Podział", "Video Tor-nonTor",
                          "Video VPN-nonVPN"], rows, numeric_from=3)


def e3_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    t = e3_summary(inputs).set_index(["feature_set", "task", "model"])
    rows = [[FEATURE_SET_LABELS[fs], MODEL_LABELS[m],
             *[_pm(t.loc[(fs, task, m), "mean"], t.loc[(fs, task, m), "std"])
               for task, _ in E3_VARIANTS]]
            for fs in ["all", "bez_idle", "bez_skrotow"] for m in MODELS]
    paired = paired_vpn_difference(inputs["e3"])
    prows = [[FEATURE_SET_LABELS[r.feature_set], MODEL_LABELS[r.model],
              " · ".join(_signed(v) for v in r.diff_folds), _signed(r.diff_mean)]
             for r in paired[paired["model"] != "dummy"].itertuples()]
    return (_section("T3", "E3: VoIP vs Video a tunel VPN (F1 makro, 3 foldy po sesjach)", ["e3"])
            + _rows(["Zestaw cech", "Model", *[label for _, label in E3_VARIANTS]], rows, 2)
            + ["Zwykły → VPN minus VPN → VPN, parami po foldach (te same foldy testowe VPN):", ""]
            + _rows(["Zestaw cech", "Model", "per fold", "średnia"], prows, 2))


def e4_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    t = e4_summary(inputs).set_index(["feature_set", "task", "model"])
    rows = [[FEATURE_SET_LABELS[fs], MODEL_LABELS[m],
             *[_pm(t.loc[(fs, task, m), "mean"], t.loc[(fs, task, m), "std"]) for task in TASKS]]
            for fs in FEATURE_SET_LABELS for m in MODELS]
    imp = e4_importance(inputs).set_index(["feature_set", "task", "group"])["perm_mean"]
    irows = [[FEATURE_SET_LABELS[fs], GROUP_LABELS[g],
              *[_signed(imp[(fs, task, g)]) for task in TASKS]]
             for fs in ["all", "bez_skrotow"] for g in GROUP_LABELS
             if all((fs, task, g) in imp.index for task in TASKS)]
    header_tasks = [TASK_SHORT[task] for task in TASKS]
    return (_section("T4", "E4: zestawy cech (F1 makro, po sesjach)", ["e4", "e4_importance"])
            + _rows(["Zestaw cech", "Model", *header_tasks], rows, 2)
            + ["Ważność permutacyjna grup cech (RF, spadek F1 makro po permutacji grupy):", ""]
            + _rows(["Zestaw cech", "Grupa", *header_tasks], irows, 2))


def e5_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    shares = e5_shares(inputs)
    rows = [[MODEL_LABELS[r.model], r.campaign, r.tunnel, str(r.total),
             *[f"{100 * getattr(r, f'share_{s}'):.1f}".replace(".", ",")
               for s in ("WWW", "VoIP", "Video")]]
            for r in _ordered(shares, campaign=["tor-nontor", "vpn-nonvpn"],
                              tunnel=["plain", "vpn"], model=MODELS).itertuples()]
    return (_section("T5", "E5: Audio przez potoki 3 usług (% przepływów)", ["e5"])
            + _rows(["Model", "Kampania", "Tunel", "Przepływy", "% WWW", "% VoIP", "% Video"],
                    rows, 3))


def _n_label(n: int) -> str:
    return "pełny" if n == 0 else str(n)


def e6_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    curve = _ordered(e6_curve(inputs), population=E6_POPULATIONS, model=MODELS,
                     n_first=E6_N_ORDER)
    rows = [[r.population, MODEL_LABELS[r.model], _n_label(r.n_first),
             _pm(r.f1_macro_mean, r.f1_macro_std),
             _pm(r.balanced_accuracy_mean, r.balanced_accuracy_std), str(r.n_folds)]
            for r in curve.itertuples()]
    paired = _ordered(e6_paired(inputs), population=E6_POPULATIONS, model=MODELS,
                      n_first=E6_N_ORDER)
    prows = [[r.population, MODEL_LABELS[r.model], str(r.n_first),
              f"{_signed(r.mean)} ± {_num(r.std)}",
              f"{_signed(r.min)} … {_signed(r.max)}"]
             for r in paired[paired["model"] != "dummy"].itertuples()]
    return (_section("T6", "E6: VoIP vs Video z pierwszych N pakietów", ["e6", "e6_folds"],
                     "Populacji `wszystkie` (5 foldów) i `min20` (3 foldy) nie zestawiamy.")
            + _rows(["Populacja", "Model", "N", "F1 makro", "Dokładność zbalansowana", "Foldy"],
                    rows, 3)
            + ["Różnica F1 makro N − pełny przepływ, parami po foldach:", ""]
            + _rows(["Populacja", "Model", "N", "średnia ± odchylenie", "zakres po foldach"],
                    prows, 3))


def e7_section(inputs: dict[str, pd.DataFrame]) -> list[str]:
    e7 = e7_compare(inputs)
    rows = [[TASK_SHORT[r.task], MODEL_LABELS[r.model], _pm(r.cv_f1_macro, r.cv_f1_macro_std),
             _num(r.f1_macro), _num(r.balanced_accuracy), _num(r.f1_macro_majority)]
            for r in e7.itertuples() if r.model in TRAINED]
    return (_section("T7", "E7: CIC-Darknet2020 → USBVPN2022 (tylko test)", ["e7"],
                     "CV = E4 bez skrótów, po sesjach. VoIP w USBVPN2022: 62 przepływy z "
                     "jednego spotkania.")
            + _rows(["Zadanie", "Model", "F1 makro CV", "F1 makro USBVPN2022",
                     "Dokładność zbalansowana USBVPN2022", "F1 klasy większości"], rows, 2))


def tables_markdown(inputs: dict[str, pd.DataFrame],
                    video_recall: dict[str, pd.DataFrame]) -> str:
    lines = ["# Tabele wyników (etap 08)", "",
             "Wygenerowane przez `src/make_figures_08.py` z plików w `reports/results/`; "
             "nie edytować ręcznie. Średnia ± odchylenie po foldach zewnętrznych.", "",
             *main_section(inputs), *campaign_section(inputs, video_recall),
             *e3_section(inputs), *e4_section(inputs), *e5_section(inputs),
             *e6_section(inputs), *e7_section(inputs)]
    return "\n".join(lines)
