# E7, krok 2: modele z models-v1 na USBVPN2022 (ruch bez VPN)

Tylko test: potoki uczone na CIC-Darknet2020 (zestaw `bez_skrotow`), bez treningu i strojenia na USBVPN2022. „CV E4” to wynik zagnieżdżonej CV po sesjach z E4 (`e4_bez_skrotow_*`), do którego odsyła `metadata.json`; czułość CV z łącznej macierzy pomyłek po foldach. Proporcje klas w USBVPN2022 są inne niż w Darknet, więc obok F1 makro podajemy dokładność zbalansowaną (średnia czułość klas), która od proporcji nie zależy.

## WWW vs Video (kampania Tor-nonTor)

| model | F1 makro CV E4 | F1 makro USBVPN2022 | zmiana | dokł. zbalansowana | czułość WWW: CV → USBVPN [%] | czułość Video: CV → USBVPN [%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| k-NN | 0.791 ± 0.007 | 0.503 | -0.288 | 0.503 | 97.0 → 95.1 | 56.6 → 5.6 |
| drzewo | 0.782 ± 0.009 | 0.455 | -0.326 | 0.522 | 93.3 → 68.2 | 69.9 → 36.2 |
| RF | 0.797 ± 0.012 | 0.469 | -0.328 | 0.512 | 92.1 → 73.9 | 79.7 → 28.5 |

Przepływy USBVPN2022: WWW 42,797, Video 2,914. Stała odpowiedź „klasa większości” daje F1 makro 0.484, dokładność zbalansowana 0.500.

### Czułość RF według protokołu, długości przepływu i portu

| podział | wartość | WWW: czułość % (n) | Video: czułość % (n) |
| --- | --- | ---: | ---: |
| długość | 4–20 pakietów | 86.6 (15,573) | 8.5 (939) |
| długość | ≤ 3 pakiety | 82.1 (3,810) | 25.7 (393) |
| długość | ≥ 21 pakietów | 64.2 (23,414) | 41.0 (1,582) |
| port | 443 | 73.5 (42,081) | 29.9 (2,740) |
| port | 80 | 94.3 (227) | 2.8 (36) |
| port | inny | 98.4 (489) | 8.0 (138) |
| protokół | TCP | 71.5 (33,804) | 26.8 (1,839) |
| protokół | UDP | 83.2 (8,993) | 31.4 (1,075) |

### Przesunięcie cech, na których opiera się RF (top 10 wg Gini)

Średni KS ważony ważnością RF: **0.47** (bez ważenia 0.43).

| cecha | ważność RF | KS WWW | KS Video |
| --- | ---: | ---: | ---: |
| Flow IAT Max | 0.137 | 0.46 | 0.46 |
| Flow IAT Min | 0.130 | 0.68 | 0.48 |
| Fwd IAT Max | 0.099 | 0.43 | 0.47 |
| Bwd IAT Max | 0.050 | 0.35 | 0.39 |
| Fwd IAT Min | 0.048 | 0.37 | 0.33 |
| Flow IAT Mean | 0.040 | 0.53 | 0.56 |
| Fwd Packets/s | 0.038 | 0.52 | 0.55 |
| Flow IAT Std | 0.033 | 0.49 | 0.50 |
| Flow Packets/s | 0.031 | 0.53 | 0.55 |
| Fwd IAT Std | 0.031 | 0.45 | 0.38 |

## VoIP vs Video (kampania VPN-nonVPN, ruch zwykły i VPN)

| model | F1 makro CV E4 | F1 makro USBVPN2022 | zmiana | dokł. zbalansowana | czułość VoIP: CV → USBVPN [%] | czułość Video: CV → USBVPN [%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| k-NN | 0.942 ± 0.016 | 0.487 | -0.455 | 0.488 | 89.3 → 4.8 | 99.0 → 92.7 |
| drzewo | 0.926 ± 0.040 | 0.532 | -0.394 | 0.531 | 89.5 → 8.1 | 98.1 → 98.2 |
| RF | 0.957 ± 0.022 | 0.545 | -0.412 | 0.546 | 92.1 → 11.3 | 99.2 → 98.0 |

Przepływy USBVPN2022: VoIP 62, Video 2,914. Stała odpowiedź „klasa większości” daje F1 makro 0.495, dokładność zbalansowana 0.500.

### Czułość RF według protokołu, długości przepływu i portu

| podział | wartość | VoIP: czułość % (n) | Video: czułość % (n) |
| --- | --- | ---: | ---: |
| długość | 4–20 pakietów | 0.0 (19) | 99.8 (939) |
| długość | ≤ 3 pakiety | 50.0 (14) | 85.5 (393) |
| długość | ≥ 21 pakietów | 0.0 (29) | 100.0 (1,582) |
| port | 443 | 6.2 (48) | 99.2 (2,740) |
| port | 80 | 0.0 (4) | 94.4 (36) |
| port | inny | 40.0 (10) | 74.6 (138) |
| protokół | TCP | 17.9 (39) | 96.8 (1,839) |
| protokół | UDP | 0.0 (23) | 100.0 (1,075) |

### Przesunięcie cech, na których opiera się RF (top 10 wg Gini)

Średni KS ważony ważnością RF: **0.42** (bez ważenia 0.42).

| cecha | ważność RF | KS VoIP | KS Video |
| --- | ---: | ---: | ---: |
| ACK Flag Count | 0.055 | 0.30 | 0.31 |
| Packet Length Min | 0.053 | 0.41 | 0.33 |
| Protocol | 0.048 | 0.25 | 0.31 |
| Fwd Packet Length Min | 0.043 | 0.38 | 0.33 |
| Subflow Fwd Bytes | 0.037 | 0.29 | 0.50 |
| Fwd Segment Size Avg | 0.037 | 0.32 | 0.56 |
| Fwd Header Length | 0.035 | 0.27 | 0.49 |
| Fwd Packet Length Mean | 0.032 | 0.32 | 0.56 |
| Bwd Header Length | 0.032 | 0.28 | 0.45 |
| Bwd Packet Length Min | 0.029 | 0.38 | 0.32 |

## WWW / VoIP / Video (ruch zwykły)

| model | F1 makro CV E4 | F1 makro USBVPN2022 | zmiana | dokł. zbalansowana | czułość WWW: CV → USBVPN [%] | czułość VoIP: CV → USBVPN [%] | czułość Video: CV → USBVPN [%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| k-NN | 0.717 ± 0.088 | 0.270 | -0.447 | 0.389 | 95.9 → 50.1 | 31.9 → 1.6 | 73.4 → 64.9 |
| drzewo | 0.698 ± 0.092 | 0.114 | -0.584 | 0.348 | 94.7 → 11.9 | 34.8 → 4.8 | 81.9 → 87.5 |
| RF | 0.713 ± 0.095 | 0.108 | -0.605 | 0.363 | 95.0 → 9.0 | 36.3 → 3.2 | 86.6 → 96.5 |

Przepływy USBVPN2022: WWW 42,797, VoIP 62, Video 2,914. Stała odpowiedź „klasa większości” daje F1 makro 0.322, dokładność zbalansowana 0.333.

### Czułość RF według protokołu, długości przepływu i portu

| podział | wartość | WWW: czułość % (n) | VoIP: czułość % (n) | Video: czułość % (n) |
| --- | --- | ---: | ---: | ---: |
| długość | 4–20 pakietów | 10.2 (15,573) | 0.0 (19) | 97.8 (939) |
| długość | ≤ 3 pakiety | 26.5 (3,810) | 14.3 (14) | 81.7 (393) |
| długość | ≥ 21 pakietów | 5.4 (23,414) | 0.0 (29) | 99.4 (1,582) |
| port | 443 | 8.9 (42,081) | 0.0 (48) | 98.0 (2,740) |
| port | 80 | 33.0 (227) | 0.0 (4) | 63.9 (36) |
| port | inny | 11.9 (489) | 20.0 (10) | 74.6 (138) |
| protokół | TCP | 11.4 (33,804) | 5.1 (39) | 94.5 (1,839) |
| protokół | UDP | 0.0 (8,993) | 0.0 (23) | 100.0 (1,075) |

### Przesunięcie cech, na których opiera się RF (top 10 wg Gini)

Średni KS ważony ważnością RF: **0.42** (bez ważenia 0.42).

| cecha | ważność RF | KS WWW | KS VoIP | KS Video |
| --- | ---: | ---: | ---: | ---: |
| Flow IAT Min | 0.070 | 0.68 | 0.52 | 0.57 |
| Fwd IAT Min | 0.054 | 0.37 | 0.67 | 0.35 |
| Bwd Packet Length Min | 0.051 | 0.22 | 0.38 | 0.35 |
| ACK Flag Count | 0.048 | 0.26 | 0.30 | 0.34 |
| Flow IAT Max | 0.042 | 0.46 | 0.28 | 0.39 |
| Fwd IAT Max | 0.041 | 0.43 | 0.28 | 0.38 |
| Protocol | 0.032 | 0.21 | 0.25 | 0.33 |
| Packet Length Min | 0.032 | 0.21 | 0.41 | 0.34 |
| Flow IAT Mean | 0.031 | 0.53 | 0.23 | 0.53 |
| Bwd IAT Max | 0.028 | 0.35 | 0.32 | 0.35 |

