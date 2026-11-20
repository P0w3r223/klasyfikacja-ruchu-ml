import numpy as np
import pandas as pd

from campaign_test import campaign_scores, campaign_video, summary


def _video(n_sessions: int = 20, per_session: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for s in range(n_sessions):
        campaign = "tor-nontor" if s % 2 else "vpn-nonvpn"
        for _ in range(per_session):
            rows.append({"session": f"s{s}", "campaign": campaign,
                         "signal": (s % 2) * 10 + rng.normal(), "noise": rng.normal()})
    return pd.DataFrame(rows)


def test_campaign_video_keeps_only_plain_video() -> None:
    flows = pd.DataFrame({"service": ["Video", "Video", "WWW"],
                          "tunnel": ["plain", "vpn", "plain"]})
    assert campaign_video(flows).index.tolist() == [0]


def test_campaign_scores_separate_signal_from_noise() -> None:
    folds = campaign_scores(_video(), {"signal": ["signal"], "noise": ["noise"]},
                            n_splits=4, seed=0, n_estimators=20)
    assert len(folds) == 8
    means = summary(folds).set_index("feature_set")["mean"]
    assert means["signal"] == 1.0
    assert means["noise"] < 0.8
