"""E7: modele z models-v1 na USBVPN2022 (zbiór z innego laboratorium i roku).

Krok 1 (`rozklady`, przed oceną modeli): porównanie rozkładów 55 cech z Darknet,
statystyka Kołmogorowa-Smirnowa per cecha i klasa. Wyniki: reports/results/06_e7/.

Użycie: python src/e7.py rozklady [--usbvpn data/external/usbvpn_flows.parquet]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from features import PROCESSED, feature_group, load_flows
from model_store import MODELS_DIR, file_sha256, load_metadata
from train import _git_state, git_provenance

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
USBVPN = ROOT / "data" / "external" / "usbvpn_flows.parquet"
RESULTS = ROOT / "reports" / "results" / "06_e7"
MTU_PAYLOAD = 1460  # największy ładunek TCP bez scalania segmentów (MSS przy MTU 1500)


def references(darknet: pd.DataFrame) -> dict[str, tuple[str, pd.DataFrame]]:
    """Zbiory odniesienia z Darknet (ruch zwykły): nazwa → (usługa, przepływy).

    WWW jest tylko w kampanii Tor-nonTor, VoIP tylko w VPN-nonVPN, Video w obu; Video
    porównujemy z każdą kampanią osobno, bo każde zadanie uczyło się na innej.
    """
    plain = darknet[darknet["tunnel"] == "plain"]
    by = lambda s, c: plain[(plain["service"] == s) & (plain["campaign"] == c)]  # noqa: E731
    return {"WWW (Tor-nonTor)": ("WWW", by("WWW", "tor-nontor")),
            "Video (Tor-nonTor)": ("Video", by("Video", "tor-nontor")),
            "Video (VPN-nonVPN)": ("Video", by("Video", "vpn-nonvpn")),
            "VoIP (VPN-nonVPN)": ("VoIP", by("VoIP", "vpn-nonvpn"))}


def ks_table(darknet: pd.DataFrame, usb: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    refs = references(darknet)
    for ref, (service, d) in refs.items():
        u = usb[usb["service"] == service]
        for f in features:
            res = ks_2samp(d[f], u[f])
            rows.append({"reference": ref, "service": service, "feature": f,
                         "group": feature_group(f), "n_darknet": len(d), "n_usbvpn": len(u),
                         "ks": res.statistic, "p_value": res.pvalue,
                         "median_darknet": d[f].median(), "median_usbvpn": u[f].median(),
                         "zero_darknet": (d[f] == 0).mean(), "zero_usbvpn": (u[f] == 0).mean()})
    # miara odniesienia: jak daleko są od siebie dwie kampanie Darknet na tym samym wideo
    _, v1 = refs["Video (Tor-nonTor)"]
    _, v2 = refs["Video (VPN-nonVPN)"]
    for f in features:
        res = ks_2samp(v1[f], v2[f])
        rows.append({"reference": "Darknet: Video Tor-nonTor vs VPN-nonVPN", "service": "Video",
                     "feature": f, "group": feature_group(f), "n_darknet": len(v1),
                     "n_usbvpn": len(v2), "ks": res.statistic, "p_value": res.pvalue,
                     "median_darknet": v1[f].median(), "median_usbvpn": v2[f].median(),
                     "zero_darknet": (v1[f] == 0).mean(), "zero_usbvpn": (v2[f] == 0).mean()})
    return pd.DataFrame(rows)


def profile(df: pd.DataFrame, name: str) -> dict[str, Any]:
    """Proste cechy ruchu do tabeli porównawczej (protokoły, scalone segmenty, czas, rozmiar)."""
    big = (df["Fwd Packet Length Max"] > MTU_PAYLOAD) | (df["Bwd Packet Length Max"] > MTU_PAYLOAD)
    n = df["Total Fwd Packet"] + df["Total Bwd packets"]
    size = df["Total Length of Fwd Packet"] + df["Total Length of Bwd Packet"]
    tcp = df["Protocol"] == 6
    pct = lambda m: 100 * m[tcp].mean() if tcp.any() else float("nan")  # noqa: E731
    return {"zbiór": name, "przepływy": len(df), "% UDP": 100 * (~tcp).mean(),
            f"% z ładunkiem > {MTU_PAYLOAD} B": 100 * big.mean(),
            "mediana pakietów": n.median(), "mediana bajtów": size.median(),
            "mediana czasu [s]": df["Flow Duration"].median() / 1e6,
            "% ≤ 3 pakiety": 100 * (n <= 3).mean(),
            "% przerwa > 1 s": 100 * (df["Flow IAT Max"] > 1e6).mean(),
            "TCP: % bez ładunku": pct(size == 0),
            "TCP: % z SYN": pct(df["SYN Flag Count"] > 0),
            "TCP: % z FIN": pct(df["FIN Flag Count"] > 0)}


def heatmap(ks: pd.DataFrame, path: Path) -> None:
    piv = ks.pivot(index="feature", columns="reference", values="ks")
    order = list(references(pd.DataFrame(columns=["tunnel", "service", "campaign"]))) + [
        "Darknet: Video Tor-nonTor vs VPN-nonVPN"]
    piv = piv[order]
    piv = piv.loc[piv.iloc[:, :4].mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(8.5, 15))
    im = ax.imshow(piv.to_numpy(), cmap="viridis", vmin=0, vmax=1, aspect="auto")
    labels = [o.replace(" (", "\n(") for o in order[:4]] + ["Darknet:\nVideo Tor-nonTor\nvs VPN-nonVPN"]
    ax.set_xticks(range(len(order)), labels, fontsize=7)
    ax.set_yticks(range(len(piv)), piv.index, fontsize=7)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6,
                    color="black" if v > 0.6 else "white")
    fig.colorbar(im, ax=ax, fraction=0.04, label="statystyka KS (0 = te same rozkłady)")
    ax.set_title("E7: USBVPN2022 vs Darknet, statystyka KS per cecha\n"
                 "(ostatnia kolumna: dwie kampanie Darknet na wideo, dla skali)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def markdown(ks: pd.DataFrame, prof: pd.DataFrame) -> str:
    main = ks[~ks["reference"].str.startswith("Darknet")]
    piv = ks.pivot(index="feature", columns="reference", values="ks")
    cols = list(main["reference"].unique()) + ["Darknet: Video Tor-nonTor vs VPN-nonVPN"]
    piv = piv[cols].assign(średnia=piv[cols[:4]].mean(axis=1)).sort_values("średnia",
                                                                            ascending=False)
    grp = ks.groupby(["group", "reference"])["ks"].mean().unstack()[cols]
    lines = ["# E7, krok 1: rozkłady cech USBVPN2022 vs Darknet (przed oceną modeli)\n",
             "Statystyka KS: największa różnica dystrybuant (0 = te same rozkłady, 1 = rozłączne). "
             "Przy tysiącach przepływów prawie każda różnica jest istotna (p ≈ 0), więc "
             "porównujemy wielkość statystyki. Ostatnia kolumna to skala odniesienia: dwie "
             "kampanie Darknet na tym samym wideo, które RF rozróżnia z dokładnością 0,997.\n",
             "## Profil ruchu\n", prof.to_markdown(index=False, floatfmt=".1f"), "",
             "## Średnia KS w grupach cech\n", grp.to_markdown(floatfmt=".2f"), "",
             "## KS per cecha (malejąco według średniej z czterech porównań)\n",
             piv.to_markdown(floatfmt=".2f"), "",
             "## Mediany (Darknet → USBVPN2022)\n",
             "| cecha | " + " | ".join(cols[:4]) + " |",
             "| --- | " + " | ".join("---" for _ in cols[:4]) + " |"]
    med = main.set_index(["feature", "reference"])
    for f in piv.index:
        cells = [f"{med.loc[(f, c), 'median_darknet']:.4g} → {med.loc[(f, c), 'median_usbvpn']:.4g}"
                 for c in cols[:4]]
        lines.append(f"| {f} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def cmd_rozklady(args: argparse.Namespace) -> None:
    meta = load_metadata(args.models_dir)
    features = meta["features"]
    git_before = _git_state()
    darknet = load_flows(path=args.data)
    usb = pd.read_parquet(args.usbvpn)
    ks = ks_table(darknet, usb, features)
    refs = references(darknet)
    prof = pd.DataFrame(
        [profile(d, f"Darknet {name}") for name, (_, d) in refs.items()]
        + [profile(usb[usb["service"] == s], f"USBVPN2022 {s}") for s in ["WWW", "Video", "VoIP"]])
    git = git_provenance(git_before, _git_state())

    args.out.mkdir(parents=True, exist_ok=True)
    ks.to_csv(args.out / "ks_cechy.csv", index=False)
    prof.to_csv(args.out / "profil_ruchu.csv", index=False)
    (args.out / "rozklady.md").write_text(markdown(ks, prof), encoding="utf-8")
    heatmap(ks, args.out / "ks_heatmap.png")
    (args.out / "run_rozklady.json").write_text(json.dumps({
        "step": "rozklady", "darknet": {"path": args.data.name, "sha256": file_sha256(args.data)},
        "usbvpn": {"path": args.usbvpn.name, "sha256": file_sha256(args.usbvpn),
                   "n_flows": len(usb)},
        "features": len(features), **git}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(prof.to_string(index=False))
    print(ks.groupby("reference")["ks"].describe().round(2).to_string())
    print(f"Wyniki: {args.out}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rozklady", help="KS per cecha i klasa, przed oceną modeli")
    r.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    r.add_argument("--usbvpn", type=Path, default=USBVPN)
    r.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    r.add_argument("--out", type=Path, default=RESULTS)
    args = ap.parse_args(argv)
    if args.cmd == "rozklady":
        cmd_rozklady(args)


if __name__ == "__main__":
    sys.exit(main())
