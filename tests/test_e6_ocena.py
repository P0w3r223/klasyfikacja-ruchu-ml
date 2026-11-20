"""Ocena E6: populacje, sesje i foldy wspólne dla wariantów N (etap 07)."""
import numpy as np
import pandas as pd
import pytest

from e6 import FULL_FLOW
from e6_ocena import (Population, evaluate_variant, markdown_report, population_counts,
                      summarize, variant_frame, with_sessions)
from usbvpn import FEATURES

N_VARIANTS = (5, FULL_FLOW)
POP = Population("test", 0, (5,), 2)


def synthetic_prefixes(sessions_per_class=8, flows_per_session=4, seed=0):
    """Każda sesja to inna para IP; VoIP i Video różnią się średnią cech (klasy rozdzielne)."""
    rng = np.random.default_rng(seed)
    rows = []
    for c, service in enumerate(("VoIP", "Video")):
        for s in range(sessions_per_class):
            for f in range(flows_per_session):
                key = {"source_file": "a.pcap", "Src IP": f"10.{c}.{s}.1", "Src Port": 1000 + f,
                       "Dst IP": "2.2.2.2", "Dst Port": 443, "ts_us": 1_000_000 * f,
                       "n_packets": 10 + 20 * (f % 2), "traffic_type": ("NonVPN", "VPN")[s % 2],
                       "service": service}
                for n in N_VARIANTS:
                    feats = rng.normal(5.0 * c, 0.1, len(FEATURES))
                    rows.append({**key, "n_first": n, **dict(zip(FEATURES, feats))})
    return pd.DataFrame(rows)


def test_sessions_shared_by_variants_of_one_flow():
    df = with_sessions(synthetic_prefixes())
    per_flow = df.groupby(["Src IP", "Src Port"])["session"].nunique()
    assert (per_flow == 1).all()
    assert df["session"].nunique() == 16


def test_sessions_split_by_gap():
    df = synthetic_prefixes(sessions_per_class=1, flows_per_session=2)
    late = df["Src Port"] == 1001
    df.loc[late, "ts_us"] = df.loc[late, "ts_us"] + 6 * 60 * 1_000_000
    assert with_sessions(df)["session"].nunique() == 4  # 2 klasy × 2 sesje


def test_variant_frame_filters_min_packets_and_keeps_order():
    df = with_sessions(synthetic_prefixes())
    a = variant_frame(df, Population("p", 20, (5,), 2), 5)
    b = variant_frame(df, Population("p", 20, (5,), 2), FULL_FLOW)
    assert (a["n_packets"] >= 20).all() and len(a) == len(df) / 4
    pd.testing.assert_frame_equal(a[["Src IP", "Src Port"]], b[["Src IP", "Src Port"]])
    with pytest.raises(ValueError, match="brak przepływów"):
        variant_frame(df, Population("p", 1000, (5,), 2), 5)


def test_evaluate_variants_same_folds_and_metrics():
    # 12 sesji na klasę: foldy wewnętrzne strojenia drzewa mają sesje obu klas
    df = with_sessions(synthetic_prefixes(sessions_per_class=12))
    out = {n: evaluate_variant(variant_frame(df, POP, n), POP, n, ("dummy", "tree"), 42, 1)
           for n in N_VARIANTS}
    folds = pd.DataFrame(out[5][0] + out[FULL_FLOW][0])
    preds = pd.concat([out[5][1], out[FULL_FLOW][1]], ignore_index=True)
    tree = folds[folds["model"] == "tree"]
    assert np.allclose(tree["f1_macro"], 1.0) and np.allclose(tree["balanced_accuracy"], 1.0)
    rows = preds.groupby(["n_first", "model", "fold"])["row"].apply(sorted)
    assert rows.loc[5, "tree", 0] == rows.loc[FULL_FLOW, "tree", 0]

    summary = summarize(folds, preds)
    assert len(summary) == 4 and (summary["n_folds"] == 2).all()
    best = summary[summary["model"] == "tree"]
    assert np.allclose(best[["f1_macro_oof", "balanced_accuracy_oof"]], 1.0)


def test_report_lists_full_flow_last(monkeypatch):
    import e6_ocena
    monkeypatch.setattr(e6_ocena, "POPULATIONS", (POP,))
    df = with_sessions(synthetic_prefixes())
    rows, preds = evaluate_variant(variant_frame(df, POP, 5), POP, 5, ("dummy",), 42, 1)
    r2, p2 = evaluate_variant(variant_frame(df, POP, FULL_FLOW), POP, FULL_FLOW, ("dummy",), 42, 1)
    summary = summarize(pd.DataFrame(rows + r2), pd.concat([preds, p2]))
    text = markdown_report(summary, population_counts(df))
    assert text.index("| dummy | 5 |") < text.index("| dummy | pełny |")
    assert "Populacja test" in text


def test_figure_curves_and_render():
    import matplotlib.pyplot as plt

    from make_figures_07 import e6_figure, model_curves
    summary = pd.DataFrame([
        {"population": pop, "n_first": n, "model": m, "f1_macro_mean": v, "f1_macro_std": 0.01,
         "balanced_accuracy_mean": v, "balanced_accuracy_std": 0.01}
        for pop in ("wszystkie", "min20") for m in ("dummy", "rf")
        for n, v in ((5, 0.7), (20, 0.8), (FULL_FLOW, 0.9))])
    curves = model_curves(summary, "min20", "f1_macro")
    pts, full = curves["rf"]
    assert list(pts["n"]) == [5, 20] and full == 0.9
    plt.close(e6_figure(summary))
    with pytest.raises(ValueError, match="pełnego przepływu"):
        model_curves(summary[summary["n_first"] != FULL_FLOW], "min20", "f1_macro")
