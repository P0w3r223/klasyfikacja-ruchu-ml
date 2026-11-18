# E7, krok 1: rozkłady cech USBVPN2022 vs Darknet (przed oceną modeli)

Statystyka KS: największa różnica dystrybuant (0 = te same rozkłady, 1 = rozłączne). Przy tysiącach przepływów prawie każda różnica jest istotna (p ≈ 0), więc porównujemy wielkość statystyki. Ostatnia kolumna to skala odniesienia: dwie kampanie Darknet na tym samym wideo, które RF rozróżnia z dokładnością 0,997.

## Profil ruchu

| zbiór                      |   przepływy |   % UDP |   % z ładunkiem > 1460 B |   mediana pakietów |   mediana bajtów |   mediana czasu [s] |   % ≤ 3 pakiety |   % przerwa > 1 s |   TCP: % bez ładunku |   TCP: % z SYN |   TCP: % z FIN |
|:---------------------------|------------:|--------:|-------------------------:|-------------------:|-----------------:|--------------------:|----------------:|------------------:|---------------------:|---------------:|---------------:|
| Darknet WWW (Tor-nonTor)   |       20033 |     0.4 |                      0.0 |                6.0 |             45.0 |                 5.0 |            39.0 |              56.2 |                 48.0 |           51.4 |           86.0 |
| Darknet Video (Tor-nonTor) |        2364 |     2.1 |                      0.0 |                8.0 |            154.0 |                20.3 |            33.1 |              70.9 |                 36.8 |           34.3 |           63.9 |
| Darknet Video (VPN-nonVPN) |        2712 |     6.3 |                      8.8 |                5.0 |              0.0 |                 9.6 |            41.5 |              57.2 |                 56.3 |           19.4 |           63.4 |
| Darknet VoIP (VPN-nonVPN)  |         204 |    62.3 |                      0.0 |               12.0 |           1317.0 |                 7.0 |            20.6 |              21.6 |                 53.2 |           53.2 |           93.5 |
| USBVPN2022 WWW             |       42797 |    21.0 |                      0.0 |               24.0 |           7401.0 |                 0.1 |             8.9 |              11.6 |                 11.0 |           81.2 |           31.0 |
| USBVPN2022 Video           |        2914 |    36.9 |                      0.0 |               25.0 |           8250.0 |                 0.1 |            13.5 |              28.3 |                 22.6 |           79.6 |           33.1 |
| USBVPN2022 VoIP            |          62 |    37.1 |                      0.0 |               20.0 |           7991.0 |                 1.4 |            22.6 |              48.4 |                 30.8 |           71.8 |           30.8 |

## Średnia KS w grupach cech

| group        |   WWW (Tor-nonTor) |   Video (Tor-nonTor) |   Video (VPN-nonVPN) |   VoIP (VPN-nonVPN) |   Darknet: Video Tor-nonTor vs VPN-nonVPN |
|:-------------|-------------------:|---------------------:|---------------------:|--------------------:|------------------------------------------:|
| czasowe      |               0.44 |                 0.44 |                 0.39 |                0.37 |                                      0.18 |
| licznosci    |               0.36 |                 0.32 |                 0.41 |                0.23 |                                      0.13 |
| rozmiarowe   |               0.47 |                 0.47 |                 0.58 |                0.46 |                                      0.20 |
| tcp_protokol |               0.23 |                 0.23 |                 0.25 |                0.20 |                                      0.11 |
| tempo        |               0.62 |                 0.61 |                 0.56 |                0.32 |                                      0.15 |

## KS per cecha (malejąco według średniej z czterech porównań)

| feature                    |   WWW (Tor-nonTor) |   Video (Tor-nonTor) |   Video (VPN-nonVPN) |   VoIP (VPN-nonVPN) |   Darknet: Video Tor-nonTor vs VPN-nonVPN |   średnia |
|:---------------------------|-------------------:|---------------------:|---------------------:|--------------------:|------------------------------------------:|----------:|
| Bwd Bulk Rate Avg          |               0.71 |                 0.73 |                 0.69 |                0.64 |                                      0.18 |      0.69 |
| Packet Length Mean         |               0.60 |                 0.55 |                 0.68 |                0.61 |                                      0.22 |      0.61 |
| Average Packet Size        |               0.60 |                 0.56 |                 0.68 |                0.59 |                                      0.22 |      0.61 |
| Subflow Bwd Bytes          |               0.54 |                 0.56 |                 0.70 |                0.57 |                                      0.26 |      0.59 |
| Bwd Packet Length Mean     |               0.54 |                 0.57 |                 0.69 |                0.57 |                                      0.24 |      0.59 |
| Bwd Segment Size Avg       |               0.54 |                 0.57 |                 0.69 |                0.57 |                                      0.24 |      0.59 |
| Flow Bytes/s               |               0.78 |                 0.64 |                 0.61 |                0.32 |                                      0.21 |      0.59 |
| Packet Length Variance     |               0.57 |                 0.51 |                 0.67 |                0.60 |                                      0.27 |      0.59 |
| Packet Length Std          |               0.57 |                 0.51 |                 0.67 |                0.60 |                                      0.27 |      0.59 |
| Flow IAT Min               |               0.68 |                 0.48 |                 0.66 |                0.52 |                                      0.33 |      0.58 |
| Fwd Packet Length Max      |               0.56 |                 0.51 |                 0.62 |                0.61 |                                      0.21 |      0.58 |
| Bwd Packet Length Max      |               0.53 |                 0.50 |                 0.67 |                0.58 |                                      0.30 |      0.57 |
| Packet Length Max          |               0.53 |                 0.46 |                 0.64 |                0.60 |                                      0.28 |      0.56 |
| Bwd Packet Length Std      |               0.44 |                 0.44 |                 0.60 |                0.58 |                                      0.31 |      0.52 |
| Total Length of Bwd Packet |               0.53 |                 0.55 |                 0.69 |                0.27 |                                      0.25 |      0.51 |
| Fwd Packet Length Std      |               0.45 |                 0.49 |                 0.58 |                0.51 |                                      0.19 |      0.51 |
| Bwd Packet/Bulk Avg        |               0.61 |                 0.50 |                 0.62 |                0.29 |                                      0.16 |      0.51 |
| Bwd Packets/s              |               0.54 |                 0.56 |                 0.53 |                0.21 |                                      0.14 |      0.46 |
| Fwd Packet Length Mean     |               0.48 |                 0.47 |                 0.56 |                0.32 |                                      0.16 |      0.46 |
| Fwd Segment Size Avg       |               0.48 |                 0.47 |                 0.56 |                0.32 |                                      0.16 |      0.46 |
| Total Length of Fwd Packet |               0.52 |                 0.43 |                 0.60 |                0.28 |                                      0.20 |      0.46 |
| Flow IAT Mean              |               0.53 |                 0.56 |                 0.51 |                0.23 |                                      0.13 |      0.45 |
| Flow Packets/s             |               0.53 |                 0.55 |                 0.49 |                0.22 |                                      0.13 |      0.45 |
| Bwd IAT Min                |               0.29 |                 0.35 |                 0.43 |                0.71 |                                      0.14 |      0.45 |
| Fwd Packets/s              |               0.52 |                 0.55 |                 0.47 |                0.22 |                                      0.13 |      0.44 |
| Fwd Act Data Pkts          |               0.55 |                 0.37 |                 0.54 |                0.29 |                                      0.18 |      0.44 |
| Fwd IAT Min                |               0.37 |                 0.33 |                 0.36 |                0.67 |                                      0.11 |      0.44 |
| Total Bwd packets          |               0.47 |                 0.42 |                 0.57 |                0.28 |                                      0.19 |      0.43 |
| Fwd IAT Mean               |               0.52 |                 0.57 |                 0.39 |                0.22 |                                      0.19 |      0.42 |
| Subflow Fwd Bytes          |               0.45 |                 0.44 |                 0.50 |                0.29 |                                      0.12 |      0.42 |
| Fwd IAT Std                |               0.45 |                 0.38 |                 0.46 |                0.37 |                                      0.26 |      0.41 |
| Total Fwd Packet           |               0.45 |                 0.38 |                 0.53 |                0.29 |                                      0.17 |      0.41 |
| Fwd Header Length          |               0.45 |                 0.41 |                 0.49 |                0.27 |                                      0.18 |      0.41 |
| Flow IAT Std               |               0.49 |                 0.50 |                 0.37 |                0.27 |                                      0.14 |      0.41 |
| Flow Duration              |               0.45 |                 0.45 |                 0.34 |                0.35 |                                      0.17 |      0.40 |
| FIN Flag Count             |               0.61 |                 0.42 |                 0.39 |                0.16 |                                      0.07 |      0.39 |
| Fwd IAT Total              |               0.43 |                 0.47 |                 0.33 |                0.35 |                                      0.20 |      0.39 |
| Flow IAT Max               |               0.46 |                 0.46 |                 0.33 |                0.28 |                                      0.21 |      0.38 |
| Bwd Header Length          |               0.42 |                 0.36 |                 0.45 |                0.28 |                                      0.13 |      0.38 |
| Bwd IAT Std                |               0.37 |                 0.34 |                 0.38 |                0.40 |                                      0.25 |      0.37 |
| Fwd IAT Max                |               0.43 |                 0.47 |                 0.29 |                0.28 |                                      0.21 |      0.37 |
| Bwd IAT Mean               |               0.42 |                 0.41 |                 0.37 |                0.26 |                                      0.10 |      0.36 |
| Bwd IAT Total              |               0.35 |                 0.43 |                 0.33 |                0.35 |                                      0.17 |      0.36 |
| Bwd IAT Max                |               0.35 |                 0.39 |                 0.30 |                0.32 |                                      0.15 |      0.34 |
| Bwd Packet Length Min      |               0.22 |                 0.38 |                 0.32 |                0.38 |                                      0.07 |      0.33 |
| Packet Length Min          |               0.21 |                 0.35 |                 0.33 |                0.41 |                                      0.04 |      0.32 |
| ACK Flag Count             |               0.26 |                 0.36 |                 0.31 |                0.30 |                                      0.21 |      0.31 |
| Fwd Packet Length Min      |               0.20 |                 0.33 |                 0.33 |                0.38 |                                      0.02 |      0.31 |
| Protocol                   |               0.21 |                 0.35 |                 0.31 |                0.25 |                                      0.04 |      0.28 |
| PSH Flag Count             |               0.29 |                 0.17 |                 0.22 |                0.26 |                                      0.21 |      0.24 |
| SYN Flag Count             |               0.13 |                 0.17 |                 0.32 |                0.25 |                                      0.15 |      0.22 |
| Down/Up Ratio              |               0.08 |                 0.16 |                 0.07 |                0.19 |                                      0.09 |      0.13 |
| Fwd PSH Flags              |               0.06 |                 0.14 |                 0.13 |                0.05 |                                      0.01 |      0.09 |
| Subflow Fwd Packets        |               0.03 |                 0.08 |                 0.09 |                0.05 |                                      0.01 |      0.06 |
| RST Flag Count             |               0.04 |                 0.03 |                 0.05 |                0.10 |                                      0.04 |      0.05 |

## Mediany (Darknet → USBVPN2022)

| cecha | WWW (Tor-nonTor) | Video (Tor-nonTor) | Video (VPN-nonVPN) | VoIP (VPN-nonVPN) |
| --- | --- | --- | --- | --- |
| Bwd Bulk Rate Avg | 0 → 1.27e+05 | 0 → 1.625e+05 | 0 → 1.625e+05 | 2481 → 5.684e+04 |
| Packet Length Mean | 20.67 → 376.1 | 30.67 → 402.5 | 0 → 402.5 | 83 → 354.1 |
| Average Packet Size | 24.35 → 394.3 | 38.5 → 425.8 | 0 → 425.8 | 83.01 → 363.6 |
| Subflow Bwd Bytes | 0 → 296 | 19 → 326 | 0 → 326 | 41 → 245 |
| Bwd Packet Length Mean | 0 → 619.5 | 30.8 → 643.1 | 0 → 643.1 | 83 → 500.9 |
| Bwd Segment Size Avg | 0 → 619.5 | 30.8 → 643.1 | 0 → 643.1 | 83 → 500.9 |
| Flow Bytes/s | 4.326 → 1.044e+05 | 41.34 → 1.177e+05 | 0 → 1.177e+05 | 2491 → 480 |
| Packet Length Variance | 453.6 → 2.97e+05 | 2635 → 2.963e+05 | 0 → 2.963e+05 | 0 → 2.7e+05 |
| Packet Length Std | 21.3 → 545 | 51.33 → 544.4 | 0 → 544.4 | 0 → 519.6 |
| Flow IAT Min | 17 → 0 | 10 → 0 | 49 → 0 | 39.5 → 1 |
| Fwd Packet Length Max | 41 → 517 | 46 → 663.5 | 0 → 663.5 | 83 → 517 |
| Bwd Packet Length Max | 0 → 1391 | 154 → 1250 | 0 → 1250 | 83 → 1250 |
| Packet Length Max | 45 → 1400 | 154 → 1250 | 0 → 1250 | 83 → 1250 |
| Bwd Packet Length Std | 0 → 534.9 | 68.87 → 551.6 | 0 → 551.6 | 0 → 508.8 |
| Total Length of Bwd Packet | 0 → 5985 | 154 → 6510 | 0 → 6510 | 516 → 5858 |
| Fwd Packet Length Std | 19.09 → 181.4 | 10.61 → 193.7 | 0 → 193.7 | 0 → 166.8 |
| Bwd Packet/Bulk Avg | 0 → 13 | 0 → 15 | 0 → 15 | 7 → 10 |
| Bwd Packets/s | 0.672 → 131.6 | 0.2818 → 147.9 | 0.2184 → 147.9 | 14.41 → 4.544 |
| Fwd Packet Length Mean | 11.53 → 84.71 | 7.848 → 91 | 0 → 91 | 83 → 73.88 |
| Fwd Segment Size Avg | 11.53 → 84.71 | 7.848 → 91 | 0 → 91 | 83 → 73.88 |
| Total Length of Fwd Packet | 41 → 1201 | 46 → 1512 | 0 → 1512 | 790.5 → 850.5 |
| Flow IAT Mean | 2.827e+05 → 3253 | 1.247e+06 → 3223 | 6.803e+05 → 3223 | 1e+04 → 2.425e+04 |
| Flow Packets/s | 3.794 → 326.3 | 0.8668 → 328.8 | 1.568 → 328.8 | 100 → 43.67 |
| Bwd IAT Min | 3 → 0 | 2 → 0 | 6 → 0 | 998 → 0 |
| Fwd Packets/s | 1.966 → 159.4 | 0.4912 → 167.3 | 0.8795 → 167.3 | 50 → 20.43 |
| Fwd Act Data Pkts | 0 → 5 | 0 → 5 | 0 → 5 | 5 → 3.5 |
| Fwd IAT Min | 33 → 13 | 25 → 13 | 39.5 → 13 | 7822 → 14 |
| Total Bwd packets | 2 → 12 | 4 → 11 | 3 → 11 | 6 → 10 |
| Fwd IAT Mean | 3.572e+05 → 6203 | 2.28e+06 → 5447 | 2.011e+05 → 5447 | 2e+04 → 3.845e+04 |
| Subflow Fwd Bytes | 5 → 42 | 3 → 42 | 0 → 42 | 41 → 34 |
| Fwd IAT Std | 3.896e+05 → 8288 | 1.694e+05 → 6823 | 32.53 → 6823 | 3126 → 4.973e+04 |
| Total Fwd Packet | 3 → 12 | 4 → 13 | 3 → 13 | 6 → 10 |
| Fwd Header Length | 72 → 288 | 80 → 276 | 96 → 276 | 112 → 200 |
| Flow IAT Std | 6.832e+05 → 6549 | 3.666e+06 → 6171 | 5.301e+05 → 6171 | 7093 → 4.118e+04 |
| Flow Duration | 4.995e+06 → 8.62e+04 | 2.03e+07 → 8.189e+04 | 9.593e+06 → 8.189e+04 | 6.991e+06 → 1.388e+06 |
| FIN Flag Count | 1 → 0 | 1 → 0 | 1 → 0 | 0 → 0 |
| Fwd IAT Total | 2.974e+06 → 7.591e+04 | 2.029e+07 → 5.769e+04 | 2.695e+06 → 5.769e+04 | 6.858e+06 → 6.85e+05 |
| Flow IAT Max | 3.19e+06 → 2.779e+04 | 1.579e+07 → 2.857e+04 | 6.3e+06 → 2.857e+04 | 2.417e+04 → 5.025e+05 |
| Bwd Header Length | 52 → 264 | 80 → 264 | 64 → 264 | 72 → 172 |
| Bwd IAT Std | 0 → 9496 | 1.743e+05 → 8869 | 25.46 → 8869 | 3114 → 4.955e+04 |
| Fwd IAT Max | 1.74e+06 → 2.597e+04 | 1.569e+07 → 2.281e+04 | 6.394e+05 → 2.281e+04 | 2.681e+04 → 2.326e+05 |
| Bwd IAT Mean | 1.343e+04 → 5603 | 2.711e+05 → 5335 | 3.749e+04 → 5335 | 2e+04 → 2.289e+04 |
| Bwd IAT Total | 3.232e+04 → 7.681e+04 | 1.402e+07 → 6.929e+04 | 3.788e+05 → 6.929e+04 | 5.316e+06 → 3.862e+05 |
| Bwd IAT Max | 3.232e+04 → 2.961e+04 | 3.397e+06 → 2.68e+04 | 1.236e+05 → 2.68e+04 | 2.602e+04 → 1.67e+05 |
| Bwd Packet Length Min | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| Packet Length Min | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| ACK Flag Count | 5 → 14 | 8 → 3 | 4 → 3 | 0 → 2 |
| Fwd Packet Length Min | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| Protocol | 6 → 6 | 6 → 6 | 6 → 6 | 17 → 6 |
| PSH Flag Count | 1 → 4 | 1 → 0 | 0 → 0 | 0 → 0 |
| SYN Flag Count | 2 → 2 | 0 → 1 | 0 → 1 | 0 → 0 |
| Down/Up Ratio | 1 → 1 | 1 → 1 | 1 → 1 | 0 → 1 |
| Fwd PSH Flags | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| Subflow Fwd Packets | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| RST Flag Count | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
