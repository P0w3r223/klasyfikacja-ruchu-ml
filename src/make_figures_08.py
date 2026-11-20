"""Zestawienie wyników (etap 08): wszystkie rysunki i tabele z reports/results/ jednym poleceniem.

    python src/make_figures_08.py

Odtwarza rysunki 08–15 funkcjami z make_figures_03b/04/04_e4/07 (bez ich tabel, które
zapisują do reports/results/), rysuje nowe 16–17 i slajdy S1–S5 (reports/figures/slajdy/)
i zapisuje reports/wyniki_tabele.md. Do reports/results/ tylko czyta. Czułość Video per
kampania (T2) potrzebuje lokalnych predictions.parquet i flows.parquet, więc całość
odtwarza się na komputerze, który liczył eksperymenty.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

import figures_08 as f8
import make_figures_03b
import make_figures_04
import make_figures_04_e4
import make_figures_07
from features import PROCESSED, load_flows
from make_figures_03b import load_campaign_recall, save_figures
from wyniki_dane import (campaign_test, e3_summary, e5_shares, e6_curve, e7_compare,
                         load_inputs, story_steps)
from wyniki_tabele import tables_markdown

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "reports" / "results"
FIGURES = ROOT / "reports" / "figures"
TABLES = ROOT / "reports" / "wyniki_tabele.md"
SLIDES_DIR = "slajdy"
SAVE_KW = {"dpi": 150}
# T2: ten sam eksperyment z przeciekiem (03b) i bez skrótów (E4)
RECALL_EXPERIMENTS = ("e1e2_uslugi3_plain", "e4_bez_skrotow_uslugi3_plain")


def report_figures(results: Path) -> list[tuple[dict[str, plt.Figure], dict]]:
    """Rysunki 08–17 z opcjami zapisu modułu, który je definiuje (te same pliki co dotąd)."""
    inputs = load_inputs(results)
    return [
        (make_figures_03b.figures(results), make_figures_03b.SAVE_KW),
        (make_figures_04.figures(results), make_figures_04.SAVE_KW),
        (make_figures_04_e4.figures(results), make_figures_04_e4.SAVE_KW),
        (make_figures_07.figures(results / "07_e6"), make_figures_07.SAVE_KW),
        ({"16_e5_audio.png": f8.e5_figure(e5_shares(inputs)),
          "17_e7_usbvpn.png": f8.e7_figure(e7_compare(inputs))}, SAVE_KW),
    ]


def slide_figures(results: Path) -> dict[str, plt.Figure]:
    inputs = load_inputs(results)
    return {"S1_os_opowiesci.png": f8.story_slide(story_steps(inputs)),
            "S2_efekt_kampanii.png": f8.campaign_slide(campaign_test(inputs)),
            "S3_e3_vpn.png": f8.e3_slide(e3_summary(inputs)),
            "S4_e6_pierwsze_pakiety.png": f8.e6_slide(e6_curve(inputs)),
            "S5_e7_inny_zbior.png": f8.e7_slide(e7_compare(inputs))}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--figures", type=Path, default=FIGURES)
    ap.add_argument("--tables", type=Path, default=TABLES)
    ap.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    args = ap.parse_args(argv)

    names = []
    for figs, save_kw in report_figures(args.results):
        save_figures(figs, args.figures, **save_kw)
        names += list(figs)
    slides = slide_figures(args.results)
    save_figures(slides, args.figures / SLIDES_DIR, **SAVE_KW)

    flows = load_flows(path=args.data)
    recall = {exp: load_campaign_recall(args.results, flows, exp) for exp in RECALL_EXPERIMENTS}
    args.tables.parent.mkdir(parents=True, exist_ok=True)
    args.tables.write_text(tables_markdown(load_inputs(args.results), recall), encoding="utf-8")
    print(f"Rysunki ({len(names)}): {', '.join(names)}")
    print(f"Slajdy ({len(slides)}): {', '.join(slides)}")
    print(f"Tabele: {args.tables}")


if __name__ == "__main__":
    sys.exit(main())
