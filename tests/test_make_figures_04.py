import pandas as pd
import pytest

from make_figures_04 import paired_vpn_difference


def test_paired_difference_matches_folds_and_classes():
    rows = []
    for task, f1 in [("voip_video_plain2vpn", [0.9, 0.8]), ("voip_video_vpn", [0.95, 0.7])]:
        for fold, value in enumerate(f1):
            rows.append({"feature_set": "bez_idle", "model": "rf", "fold": fold, "task": task,
                         "f1_macro": value, "f1_VoIP": value - 0.1, "f1_Video": value})
    row = paired_vpn_difference(pd.DataFrame(rows)).iloc[0]
    assert row["diff_folds"] == pytest.approx([-0.05, 0.1])
    assert row["diff_mean"] == pytest.approx(0.025)
    assert row["diff_VoIP"] == pytest.approx(0.025)
