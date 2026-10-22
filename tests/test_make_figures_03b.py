"""Logika tabeli etapu 03b: warianty podziału, podsumowanie i zawyżenie E1 − E2."""
import numpy as np
import pandas as pd
import pytest

from experiments import EXPERIMENTS
from make_figures_03b import (E1, E2, E2_15, E2_PAIR, e1_minus_e2, markdown_table,
                              summary_table, variant, video_recall_by_campaign)


def test_variant_names_every_03b_split():
    assert variant(EXPERIMENTS["e1e2_www_video_tor"], "random") == E1
    assert variant(EXPERIMENTS["e1e2_www_video_tor"], "session") == E2
    assert variant(EXPERIMENTS["e2_gap15_www_video_tor"], "session") == E2_15
    assert variant(EXPERIMENTS["e2_ippair_www_video_tor"], "session") == E2_PAIR


def fake_folds() -> pd.DataFrame:
    rows = []
    for var, f1 in [(E1, [0.98, 1.0]), (E2, [0.90, 0.94])]:
        for fold, value in enumerate(f1):
            rows.append({"task": "www_video_tor", "model": "rf", "variant": var, "fold": fold,
                         "f1_macro": value, "accuracy": value, "f1_WWW": value,
                         "f1_Video": value, "search_s": 1.0, "fit_s": 0.1,
                         "predict_us_per_flow": 2.0})
    return pd.DataFrame(rows)


def test_summary_and_gap():
    table = summary_table(fake_folds())
    e2 = table[table["variant"] == E2].iloc[0]
    assert e2["f1_mean"] == pytest.approx(0.92)
    assert e2["f1_folds"] == [0.90, 0.94]
    gap = e1_minus_e2(table).iloc[0]
    assert gap["gap"] == pytest.approx(0.07)
    std = np.std([0.98, 1.0], ddof=1)
    assert gap["se"] == pytest.approx(np.sqrt(std ** 2 / 2 + np.std([0.9, 0.94], ddof=1) ** 2 / 2))


def test_video_recall_is_split_by_campaign():
    population = pd.DataFrame({"campaign": ["tor-nontor", "tor-nontor", "vpn-nonvpn", "x"]})
    predictions = pd.DataFrame({"model": "rf", "split": "session", "row": [0, 1, 2, 3],
                                "y_true": ["Video", "Video", "Video", "WWW"],
                                "y_pred": ["Video", "WWW", "Video", "WWW"]})
    recall = video_recall_by_campaign(predictions, population).iloc[0]
    assert recall["tor-nontor"] == pytest.approx(0.5)
    assert recall["vpn-nonvpn"] == pytest.approx(1.0)
    assert "x" not in recall


def test_markdown_uses_decimal_commas():
    text = markdown_table(summary_table(fake_folds()))
    assert "| RF | E2 sesje 5 min | 0,920 |" in text
    assert "0,900 · 0,940" in text
