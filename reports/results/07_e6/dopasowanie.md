# E6, sesja 1: przepływy z PCAP-ów ISCX VPN-nonVPN i etykiety z Darknet.CSV

Plików: 60. Ramki i pominięcia (suma): frames 14,454,207, not_tcp_udp 8,241, packets 13,953,640, not_ipv4 492,326, connections 129,041, flows 166,113, ip_len_zero 1,499.

Dopasowanie: 5-krotka i czas startu (Darknet = UTC -3 h, tolerancja 1 s).

## Status przepływów (wszystkie pliki)

| match      |   przepływy |
|:-----------|------------:|
| brak       |      141255 |
| dopasowany |       24433 |
| duplikat   |         425 |

Kandydaci z tymi samymi licznikami pakietów: 95.3% par.

## Pokrycie wierszy Darknet (VoIP, Video; przed filtrem tła)

|                     |   darknet |   dopasowane |   pokrycie |
|:--------------------|----------:|-------------:|-----------:|
| ('NonVPN', 'Video') |      5039 |         4858 |      0.964 |
| ('NonVPN', 'VoIP')  |      2101 |         2035 |      0.969 |
| ('VPN', 'Video')    |      1144 |         1137 |      0.994 |
| ('VPN', 'VoIP')     |      1167 |         1111 |      0.952 |

## Po filtrze tła i czyszczeniu (jak preprocess.py)

voip_video: 9,141, background: 5,007, invalid: 0, duplicates: 151, conflicts: 64, final: 3,983

|                     |   przepływy |
|:--------------------|------------:|
| ('NonVPN', 'Video') |        2612 |
| ('NonVPN', 'VoIP')  |         202 |
| ('VPN', 'Video')    |         982 |
| ('VPN', 'VoIP')     |         187 |

## Zgodność cech pełnego przepływu z Darknet.CSV (po czyszczeniu)

`rowne`: równe co do zaokrąglenia; `w_1proc`: różnica ≤ 1% albo ≤ 1 jednostki.

|                            |   rowne |   w_1proc |
|:---------------------------|--------:|----------:|
| (wszystkie 55 naraz)       |  0.9551 |    0.9709 |
| Fwd Packets/s              |  0.9586 |    0.9955 |
| Total Fwd Packet           |  0.9588 |    0.9985 |
| Fwd Header Length          |  0.9588 |    0.9839 |
| Fwd IAT Mean               |  0.9591 |    0.9844 |
| Bwd Packets/s              |  0.9608 |    0.9977 |
| Bwd Header Length          |  0.9611 |    0.9862 |
| Fwd IAT Std                |  0.9611 |    0.9862 |
| Total Bwd packets          |  0.9611 |    1      |
| Total Length of Fwd Packet |  0.9631 |    0.9849 |
| Bwd IAT Mean               |  0.9633 |    0.9887 |
| Total Length of Bwd Packet |  0.9656 |    0.9902 |
| Bwd IAT Std                |  0.9674 |    0.9935 |
| Fwd IAT Total              |  0.9676 |    0.995  |
| Bwd IAT Total              |  0.9679 |    0.9902 |

Pełna tabela: `zgodnosc_cech.csv`; na plik: `dopasowanie_pliki.csv`.
