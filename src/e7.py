"""E7: modele z models-v1 na USBVPN2022 (zbiór z innego laboratorium i roku).

Krok 1 (`rozklady`, przed oceną modeli): porównanie rozkładów 55 cech z Darknet,
statystyka Kołmogorowa-Smirnowa per cecha i klasa. Wyniki: reports/results/06_e7/.
Krok 2 (`ocena`): 9 potoków z models-v1 na USBVPN2022 obok CV z E4 (src/e7_ocena.py);
wyniki w reports/results/06_e7/ocena/. `demo`: pliki do pokazu w formacie Darknet.CSV
(reports/results/06_e7/demo/, wejście aplikacji z etapu 09).

Użycie: python src/e7.py rozklady | ocena | demo [--usbvpn data/external/usbvpn_flows.parquet]
"""
import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from darknet_csv import SERVICE_LABELS, sample_per_service, to_darknet_frame
from e7_ocena import (cv_reference, feature_shift, majority_baseline, metrics, ocena_markdown,
                      recall_breakdown, task_population)
from features import PROCESSED, feature_group, load_flows
from model_store import (MODELS_DIR, check_versions, file_sha256, load_metadata, load_pipeline,
                         missing_input_columns)
from preprocess import background_reason
from train import RESULTS as TRAIN_RESULTS
from train import _git_state, git_provenance

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
USBVPN = ROOT / "data" / "external" / "usbvpn_flows.parquet"
RESULTS = ROOT / "reports" / "results" / "06_e7"
MTU_PAYLOAD = 1460  # największy ładunek TCP bez scalania segmentów (MSS przy MTU 1500)
# Pliki do pokazu: po jednym na zadanie główne, najwyżej kilka MB (trafiają do repo).
# VoIP ma 62 przepływy, więc bierzemy wszystkie. Etykieta ruchu „NonVPN”: pliki „Non VPN”.
DEMO_FILES = {"usbvpn2022_www_video.csv": {"WWW": 300, "Video": 300},
              "usbvpn2022_voip_video.csv": {"VoIP": 62, "Video": 300}}
DEMO_SEED = 42
DEMO_TRAFFIC_TYPE = "NonVPN"


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


def evaluate_all(usb: pd.DataFrame, meta: dict[str, Any], models_dir: Path,
                 cv_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """9 potoków na USBVPN2022 → (metryki, rozbicie czułości, predykcje, macierze pomyłek)."""
    rows, breakdowns, preds, confusion = [], [], [], {}
    features = meta["features"]
    for entry in meta["pipelines"]:
        task, model, classes = entry["task"], entry["model"], entry["classes"]
        pop = task_population(usb, classes)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            y_pred = load_pipeline(entry, models_dir).predict(pop[features])
        y_true = pop["service"].to_numpy()
        m = metrics(y_true, y_pred, classes)
        confusion[f"{task}/{model}"] = {"classes": classes, "matrix": m.pop("confusion")}
        cv = cv_reference(cv_dir / entry["reported_cv"]["experiment"], model, classes)
        rows.append({"task": task, "model": model, **m,
                     "f1_macro_majority": majority_baseline(y_true, classes),
                     **{f"cv_{k}": v for k, v in cv.items()}})
        breakdowns.append(recall_breakdown(pop, y_pred, classes).assign(task=task, model=model))
        preds.append(pd.DataFrame({"task": task, "model": model, "row": pop.index,
                                   "y_true": y_true, "y_pred": y_pred}))
    return (pd.DataFrame(rows), pd.concat(breakdowns, ignore_index=True),
            pd.concat(preds, ignore_index=True), confusion)


def rf_importances(meta: dict[str, Any], models_dir: Path) -> dict[str, pd.Series]:
    out = {}
    for entry in meta["pipelines"]:
        if entry["model"] == "rf":
            clf = load_pipeline(entry, models_dir).named_steps["clf"]
            out[entry["task"]] = pd.Series(clf.feature_importances_, index=meta["features"])
    return out


def confusion_figure(confusion: dict, tasks: dict[str, Any], path: Path) -> None:
    """Macierze pomyłek znormalizowane w wierszach (czułość na przekątnej), zadanie × model."""
    task_ids = list(tasks)
    models = ["knn", "tree", "rf"]
    names = {"knn": "k-NN", "tree": "drzewo", "rf": "RF"}
    fig, axes = plt.subplots(len(task_ids), len(models), figsize=(10, 10))
    for i, task in enumerate(task_ids):
        for j, model in enumerate(models):
            ax, c = axes[i, j], confusion[f"{task}/{model}"]
            mat = np.asarray(c["matrix"], dtype=float)
            share = mat / mat.sum(axis=1, keepdims=True)
            ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
            for r in range(len(mat)):
                for k in range(len(mat)):
                    ax.text(k, r, f"{100 * share[r, k]:.0f}%\n({int(mat[r, k])})",
                            ha="center", va="center", fontsize=7,
                            color="white" if share[r, k] > 0.6 else "black")
            ax.set_xticks(range(len(mat)), c["classes"], fontsize=7)
            ax.set_yticks(range(len(mat)), c["classes"], fontsize=7)
            ax.set_title(f"{tasks[task]['title'].split(' (')[0]}, {names[model]}", fontsize=8)
            if j == 0:
                ax.set_ylabel("prawdziwa klasa", fontsize=7)
            if i == len(task_ids) - 1:
                ax.set_xlabel("przewidziana klasa", fontsize=7)
    fig.suptitle("E7: modele z CIC-Darknet2020 na USBVPN2022 (ruch bez VPN)\n"
                 "odsetek w wierszu = czułość klasy; w nawiasie liczba przepływów", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def cmd_ocena(args: argparse.Namespace) -> None:
    meta = load_metadata(args.models_dir)
    check_versions(meta)
    git_before = _git_state()
    usb = pd.read_parquet(args.usbvpn)
    ks = pd.read_csv(args.ks)
    res, breakdown, preds, confusion = evaluate_all(usb, meta, args.models_dir, args.cv_dir)
    shift = pd.concat([feature_shift(imp, ks, task).assign(task=task)
                       for task, imp in rf_importances(meta, args.models_dir).items()])
    git = git_provenance(git_before, _git_state())

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "metryki.csv", index=False)
    breakdown.to_csv(out / "czulosc_rozbicie.csv", index=False)
    shift.rename_axis("feature").reset_index().to_csv(out / "cechy_przesuniecie.csv",
                                                      index=False)
    preds.to_parquet(out / "predictions.parquet", index=False)
    (out / "confusion.json").write_text(json.dumps(confusion, indent=1, ensure_ascii=False),
                                        encoding="utf-8")
    confusion_figure(confusion, meta["tasks"], out / "macierze_pomylek.png")
    (out / "ocena.md").write_text(ocena_markdown(res, breakdown, shift, meta["tasks"]),
                                  encoding="utf-8")
    (out / "run_ocena.json").write_text(json.dumps({
        "step": "ocena", "usbvpn": {"path": args.usbvpn.name,
                                    "sha256": file_sha256(args.usbvpn), "n_flows": len(usb)},
        "ks": args.ks.name, "models_release": meta["models_release"],
        "pipelines": {f"{e['task']}/{e['model']}": e["sha256"] for e in meta["pipelines"]},
        **git}, indent=2, ensure_ascii=False), encoding="utf-8")
    cols = ["task", "model", "f1_macro", "cv_f1_macro", "balanced_accuracy", "f1_macro_majority"]
    print(res[cols].round(3).to_string(index=False))
    print(f"Wyniki: {out}")


def cmd_demo(args: argparse.Namespace) -> None:
    meta = load_metadata(args.models_dir)
    usb = pd.read_parquet(args.usbvpn)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, counts in DEMO_FILES.items():
        sample = sample_per_service(usb, counts, seed=DEMO_SEED)
        path = args.out / name
        to_darknet_frame(sample, meta["features"], DEMO_TRAFFIC_TYPE).to_csv(path, index=False)
        check_demo_file(path, sample, meta)
        print(f"{path.name}: {len(sample)} przepływów "
              f"{sample['service'].value_counts().to_dict()}, {path.stat().st_size / 1e6:.2f} MB, "
              "kontrola kolumn OK")


def check_demo_file(path: Path, source: pd.DataFrame, meta: dict[str, Any]) -> None:
    """Plik do pokazu przechodzi kontrolę kolumn, filtr tła i ma cechy identyczne ze źródłem."""
    back = pd.read_csv(path)
    missing = missing_input_columns(list(back.columns), meta, require_label=True)
    if missing:
        raise ValueError(f"{path.name}: brak kolumn {missing}")
    removed = background_reason(back) != ""
    if removed.any():
        raise ValueError(f"{path.name}: filtr tła usunąłby {int(removed.sum())} przepływów")
    feats = meta["features"]
    # domyślny parser read_csv (jak w aplikacji) może się mylić o 1 ULP, stąd tolerancja
    if not np.allclose(back[feats].to_numpy(float), source[feats].to_numpy(float),
                       rtol=1e-12, atol=0):
        raise ValueError(f"{path.name}: cechy po zapisie do CSV różnią się od źródła")
    expected = source["service"].map(SERVICE_LABELS).to_numpy()
    if not (back[meta["label_column"]].to_numpy() == expected).all():
        raise ValueError(f"{path.name}: etykiety po zapisie różnią się od źródła")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rozklady", help="KS per cecha i klasa, przed oceną modeli")
    r.add_argument("--data", type=Path, default=PROCESSED / "flows.parquet")
    o = sub.add_parser("ocena", help="9 potoków na USBVPN2022 vs CV z E4")
    o.add_argument("--ks", type=Path, default=RESULTS / "ks_cechy.csv")
    o.add_argument("--cv-dir", type=Path, default=TRAIN_RESULTS)
    d = sub.add_parser("demo", help="pliki do pokazu w formacie Darknet.CSV")
    for p in (r, o, d):
        p.add_argument("--usbvpn", type=Path, default=USBVPN)
        p.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    r.add_argument("--out", type=Path, default=RESULTS)
    o.add_argument("--out", type=Path, default=RESULTS / "ocena")
    d.add_argument("--out", type=Path, default=RESULTS / "demo")
    args = ap.parse_args(argv)
    {"rozklady": cmd_rozklady, "ocena": cmd_ocena, "demo": cmd_demo}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
