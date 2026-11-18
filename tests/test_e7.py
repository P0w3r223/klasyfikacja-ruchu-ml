"""E7, krok 1: porównanie rozkładów cech (KS) na małych danych sztucznych."""
import numpy as np
import pandas as pd
import pytest

import e7

FEATS = ["Flow Duration", "Protocol", "Fwd Packet Length Max", "Bwd Packet Length Max",
         "Total Fwd Packet", "Total Bwd packets", "SYN Flag Count"]


def frame(service, campaign, tunnel, n, shift, seed):
    rng = np.random.default_rng(seed)
    d = {f: rng.normal(100 + shift, 10, n) for f in FEATS}
    d["Protocol"] = np.full(n, 6.0)
    return pd.DataFrame(d).assign(service=service, campaign=campaign, tunnel=tunnel)


@pytest.fixture
def darknet():
    return pd.concat([frame("WWW", "tor-nontor", "plain", 200, 0, 1),
                      frame("Video", "tor-nontor", "plain", 200, 0, 2),
                      frame("Video", "vpn-nonvpn", "plain", 200, 0, 3),
                      frame("Video", "vpn-nonvpn", "vpn", 200, 500, 4),  # VPN: poza odniesieniem
                      frame("VoIP", "vpn-nonvpn", "plain", 200, 0, 5)], ignore_index=True)


def test_ks_table_same_vs_shifted(darknet):
    usb = pd.concat([frame("WWW", "", "", 150, 0, 11),       # ten sam rozkład
                     frame("Video", "", "", 150, 100, 12),   # przesunięty o 10 odchyleń
                     frame("VoIP", "", "", 150, 0, 13)], ignore_index=True)
    ks = e7.ks_table(darknet, usb, ["Flow Duration"])
    by = ks.set_index("reference")["ks"]
    assert by["WWW (Tor-nonTor)"] < 0.2 and by["VoIP (VPN-nonVPN)"] < 0.2
    assert by["Video (Tor-nonTor)"] > 0.95 and by["Video (VPN-nonVPN)"] > 0.95
    assert by["Darknet: Video Tor-nonTor vs VPN-nonVPN"] < 0.2  # ruch VPN nie wchodzi
    assert set(ks.loc[ks["reference"] == "WWW (Tor-nonTor)", "n_darknet"]) == {200}


def test_profile_counts_offload_and_udp():
    df = pd.DataFrame({"Protocol": [6, 17, 6, 6], "Fwd Packet Length Max": [100, 1460, 2000, 0],
                       "Bwd Packet Length Max": [0, 0, 0, 5000], "Total Fwd Packet": [1, 2, 3, 4],
                       "Total Bwd packets": [1, 1, 1, 1], "Flow Duration": [1e6] * 4,
                       "SYN Flag Count": [1, 0, 0, 0], "FIN Flag Count": [0] * 4,
                       "Total Length of Fwd Packet": [1] * 4, "Total Length of Bwd Packet": [0] * 4,
                       "Flow IAT Max": [0] * 4})
    p = e7.profile(df, "x")
    assert p["% UDP"] == 25 and p["% z ładunkiem > 1460 B"] == 50 and p["% ≤ 3 pakiety"] == 50
    assert p["TCP: % z SYN"] == pytest.approx(100 / 3)
