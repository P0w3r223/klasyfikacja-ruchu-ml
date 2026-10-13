# Raport z przygotowania danych

Surowy plik: 141,530 przepływów (po pominięciu uszkodzonego wiersza 328)

### 1. Podzbiór (bez Tor, 3 usługi + Audio do E5): 63,218 przepływów

| service   |   Non-Tor |   NonVPN |   VPN |   All |
|:----------|----------:|---------:|------:|------:|
| Audio     |      1484 |     3296 | 13060 | 17840 |
| Video     |      3382 |     5039 |  1144 |  9565 |
| VoIP      |         0 |     2101 |  1167 |  3268 |
| WWW       |     32545 |        0 |     0 | 32545 |
| All       |     37411 |    10436 | 15371 | 63218 |

### Odfiltrowany ruch tła

| row_0                     |   Audio |   Video |   VoIP |   WWW |
|:--------------------------|--------:|--------:|-------:|------:|
| DHCP                      |       0 |       0 |      1 |     0 |
| DNS                       |   11571 |    3047 |    271 |  9583 |
| Dropbox LAN sync          |      32 |      56 |      0 |     0 |
| LLMNR                     |       0 |       0 |   2345 |     0 |
| NTP                       |       0 |       0 |     22 |     0 |
| NetBIOS                   |      36 |      52 |     80 |     0 |
| SNMP                      |       0 |       0 |     36 |     0 |
| SSDP                      |      26 |      29 |      0 |     0 |
| multicast/broadcast       |      33 |       3 |      0 |     0 |
| protokół inny niż TCP/UDP |     148 |     173 |    122 |    35 |

### 2. Po odfiltrowaniu ruchu tła: 35,517 przepływów

| service   |   Non-Tor |   NonVPN |   VPN |   All |
|:----------|----------:|---------:|------:|------:|
| Audio     |      1357 |     1087 |  3550 |  5994 |
| Video     |      2441 |     2728 |  1036 |  6205 |
| VoIP      |         0 |      204 |   187 |   391 |
| WWW       |     22927 |        0 |     0 | 22927 |
| All       |     26725 |     4019 |  4773 | 35517 |

Usunięte wiersze z inf/NaN: 33

Usunięte duplikaty (te same cechy i etykiety): 3,043

Przepływy o identycznych cechach, ale różnych etykietach: 255 (zostają; ograniczają osiągalną dokładność)

### 3. Po czyszczeniu: 32,441 przepływów

| service   |   Non-Tor |   NonVPN |   VPN |   All |
|:----------|----------:|---------:|------:|------:|
| Audio     |      1321 |     1081 |  3524 |  5926 |
| Video     |      2364 |     2712 |  1015 |  6091 |
| VoIP      |         0 |      204 |   187 |   391 |
| WWW       |     20033 |        0 |     0 | 20033 |
| All       |     23718 |     3997 |  4726 | 32441 |

Cechy stałe usunięte (15): Bwd PSH Flags, Fwd URG Flags, Bwd URG Flags, URG Flag Count, CWE Flag Count, ECE Flag Count, Fwd Bytes/Bulk Avg, Fwd Packet/Bulk Avg, Fwd Bulk Rate Avg, Bwd Bytes/Bulk Avg, Subflow Bwd Packets, Active Mean, Active Std, Active Max, Active Min

Cechy do modelowania: 62

### Sesje (przerwa > 5 min = nowa sesja)

|                      |   flows |   sessions |   largest_session_share |
|:---------------------|--------:|-----------:|------------------------:|
| ('Non-Tor', 'Audio') |    1321 |        265 |                    0.04 |
| ('Non-Tor', 'Video') |    2364 |        369 |                    0.04 |
| ('Non-Tor', 'WWW')   |   20033 |       3285 |                    0.01 |
| ('NonVPN', 'Audio')  |    1081 |        209 |                    0.04 |
| ('NonVPN', 'Video')  |    2712 |        462 |                    0.04 |
| ('NonVPN', 'VoIP')   |     204 |         49 |                    0.3  |
| ('VPN', 'Audio')     |    3524 |        955 |                    0.04 |
| ('VPN', 'Video')     |    1015 |        138 |                    0.13 |
| ('VPN', 'VoIP')      |     187 |         25 |                    0.17 |
