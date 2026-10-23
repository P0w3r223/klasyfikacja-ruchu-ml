# Etap 04: E4, zestawy cech i ważność grup cech

Wygenerowane przez `src/make_figures_04_e4.py` z `reports/results/e4_*` (i `e1e2_*` z 03b). Podział po sesjach, foldy jak w 03b (5, dla 3 usług 3). F1 makro: średnia ± odchylenie po foldach zewnętrznych. Zestawy poza „wszystkie” nie mają `Idle *` (przeciek daty nagrania, docs/decyzje.md). Skróty: `Idle *`, `Fwd Seg Size Min`, `FWD/Bwd Init Win Bytes`.

Ważność grup: RF z każdego foldu, liczona na jego teście. Permutacja = spadek F1 makro, gdy wszystkie kolumny grupy dostają tę samą permutację wierszy (5 powtórzeń); Gini = suma `feature_importances_` w grupie.

## WWW vs Video (Tor-nonTor)

### F1 makro dla zestawów cech

| Zestaw cech | cechy | Dummy | k-NN | drzewo | RF | ranking modeli |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| wszystkie | 62 | 0,496 ± 0,000 | 0,808 ± 0,007 | 0,892 ± 0,007 | 0,896 ± 0,009 | RF > drzewo > k-NN |
| bez Idle * | 58 | 0,496 ± 0,000 | 0,800 ± 0,009 | 0,837 ± 0,010 | 0,853 ± 0,010 | RF > drzewo > k-NN |
| bez skrótów | 55 | 0,496 ± 0,000 | 0,791 ± 0,007 | 0,782 ± 0,009 | 0,797 ± 0,012 | RF > k-NN > drzewo |
| bez Idle * i Protocol | 57 | 0,496 ± 0,000 | 0,800 ± 0,009 | 0,836 ± 0,008 | 0,852 ± 0,011 | RF > drzewo > k-NN |
| tylko czasowe | 15 | 0,496 ± 0,000 | 0,757 ± 0,011 | 0,758 ± 0,013 | 0,777 ± 0,012 | RF > drzewo > k-NN |
| czasowe + tempo | 20 | 0,496 ± 0,000 | 0,757 ± 0,016 | 0,768 ± 0,013 | 0,785 ± 0,015 | RF > drzewo > k-NN |
| tylko rozmiarowe | 22 | 0,496 ± 0,000 | 0,676 ± 0,022 | 0,680 ± 0,014 | 0,689 ± 0,012 | RF > drzewo > k-NN |

### E1/E2 z `Idle *` i bez

| Model | E1 wszystkie (03b) | E2 wszystkie (03b) | E1 − E2 | E1 bez Idle * | E2 bez Idle * | E1 − E2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dummy | 0,496 | 0,496 | 0,000 | 0,496 | 0,496 | 0,000 |
| k-NN | 0,841 | 0,808 | 0,033 | 0,832 | 0,800 | 0,032 |
| drzewo | 0,898 | 0,892 | 0,007 | 0,855 | 0,837 | 0,019 |
| RF | 0,903 | 0,896 | 0,007 | 0,871 | 0,853 | 0,018 |

### Ważność grup cech (RF)

| Grupa | cechy (wszystkie) | perm. wszystkie | perm. bez Idle * | perm. bez skrótów | Gini wszystkie | Gini bez Idle * | Gini bez skrótów |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Idle * (przeciek czasu) | 4 | 0,398 ± 0,008 | – | – | 0,454 | – | – |
| rozmiarowe | 22 | 0,074 ± 0,041 | 0,045 ± 0,007 | 0,047 ± 0,014 | 0,040 | 0,114 | 0,152 |
| czasowe (IAT, Duration) | 15 | 0,057 ± 0,029 | 0,316 ± 0,017 | 0,263 ± 0,013 | 0,272 | 0,592 | 0,661 |
| TCP i protokół | 10 | 0,023 ± 0,010 | 0,061 ± 0,010 | 0,000 ± 0,011 | 0,127 | 0,186 | 0,063 |
| liczności | 6 | 0,001 ± 0,001 | -0,001 ± 0,002 | 0,001 ± 0,006 | 0,005 | 0,018 | 0,027 |
| tempo (B/s, pakiety/s) | 5 | -0,016 ± 0,008 | -0,014 ± 0,008 | -0,040 ± 0,021 | 0,102 | 0,090 | 0,097 |

## VoIP vs Video (VPN-nonVPN)

### F1 makro dla zestawów cech

| Zestaw cech | cechy | Dummy | k-NN | drzewo | RF | ranking modeli |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| wszystkie | 62 | 0,519 ± 0,012 | 0,969 ± 0,023 | 0,979 ± 0,013 | 0,989 ± 0,006 | RF > drzewo > k-NN |
| bez Idle * | 58 | 0,519 ± 0,012 | 0,985 ± 0,007 | 0,947 ± 0,038 | 0,983 ± 0,010 | k-NN > RF > drzewo |
| bez skrótów | 55 | 0,519 ± 0,012 | 0,942 ± 0,016 | 0,926 ± 0,040 | 0,957 ± 0,022 | RF > k-NN > drzewo |
| bez Idle * i Protocol | 57 | 0,519 ± 0,012 | 0,966 ± 0,043 | 0,947 ± 0,036 | 0,979 ± 0,015 | RF > k-NN > drzewo |
| tylko czasowe | 15 | 0,519 ± 0,012 | 0,855 ± 0,084 | 0,866 ± 0,037 | 0,895 ± 0,040 | RF > drzewo > k-NN |
| czasowe + tempo | 20 | 0,519 ± 0,012 | 0,800 ± 0,091 | 0,856 ± 0,050 | 0,897 ± 0,053 | RF > drzewo > k-NN |
| tylko rozmiarowe | 22 | 0,519 ± 0,012 | 0,932 ± 0,057 | 0,917 ± 0,060 | 0,933 ± 0,040 | RF > k-NN > drzewo |

### E1/E2 z `Idle *` i bez

| Model | E1 wszystkie (03b) | E2 wszystkie (03b) | E1 − E2 | E1 bez Idle * | E2 bez Idle * | E1 − E2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dummy | 0,515 | 0,519 | -0,005 | 0,515 | 0,519 | -0,005 |
| k-NN | 0,994 | 0,969 | 0,025 | 0,990 | 0,985 | 0,005 |
| drzewo | 0,994 | 0,979 | 0,014 | 0,977 | 0,947 | 0,030 |
| RF | 0,992 | 0,989 | 0,003 | 0,987 | 0,983 | 0,004 |

### Ważność grup cech (RF)

| Grupa | cechy (wszystkie) | perm. wszystkie | perm. bez Idle * | perm. bez skrótów | Gini wszystkie | Gini bez Idle * | Gini bez skrótów |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Idle * (przeciek czasu) | 4 | 0,329 ± 0,049 | – | – | 0,322 | – | – |
| TCP i protokół | 10 | 0,258 ± 0,108 | 0,393 ± 0,032 | 0,063 ± 0,039 | 0,430 | 0,548 | 0,154 |
| czasowe (IAT, Duration) | 15 | 0,031 ± 0,026 | 0,105 ± 0,027 | 0,160 ± 0,053 | 0,100 | 0,138 | 0,294 |
| rozmiarowe | 22 | 0,008 ± 0,009 | 0,188 ± 0,054 | 0,355 ± 0,038 | 0,114 | 0,259 | 0,459 |
| liczności | 6 | -0,000 ± 0,002 | -0,000 ± 0,003 | -0,001 ± 0,003 | 0,007 | 0,010 | 0,015 |
| tempo (B/s, pakiety/s) | 5 | -0,000 ± 0,002 | 0,004 ± 0,007 | 0,003 ± 0,008 | 0,027 | 0,044 | 0,078 |

## 3 usługi, ruch zwykły (odniesienie)

### F1 makro dla zestawów cech

| Zestaw cech | cechy | Dummy | k-NN | drzewo | RF | ranking modeli |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| wszystkie | 62 | 0,336 ± 0,000 | 0,763 ± 0,106 | 0,908 ± 0,060 | 0,955 ± 0,011 | RF > drzewo > k-NN |
| bez Idle * | 58 | 0,336 ± 0,000 | 0,784 ± 0,135 | 0,816 ± 0,143 | 0,802 ± 0,124 | drzewo > RF > k-NN |
| bez skrótów | 55 | 0,336 ± 0,000 | 0,717 ± 0,088 | 0,698 ± 0,092 | 0,713 ± 0,095 | k-NN > RF > drzewo |
| bez Idle * i Protocol | 57 | 0,336 ± 0,000 | 0,784 ± 0,135 | 0,757 ± 0,131 | 0,798 ± 0,121 | RF > k-NN > drzewo |
| tylko czasowe | 15 | 0,336 ± 0,000 | 0,645 ± 0,054 | 0,625 ± 0,045 | 0,643 ± 0,061 | k-NN > RF > drzewo |
| czasowe + tempo | 20 | 0,336 ± 0,000 | 0,646 ± 0,055 | 0,645 ± 0,067 | 0,663 ± 0,062 | RF > k-NN > drzewo |
| tylko rozmiarowe | 22 | 0,336 ± 0,000 | 0,724 ± 0,098 | 0,644 ± 0,129 | 0,715 ± 0,138 | k-NN > RF > drzewo |

### E1/E2 z `Idle *` i bez

| Model | E1 wszystkie (03b) | E2 wszystkie (03b) | E1 − E2 | E1 bez Idle * | E2 bez Idle * | E1 − E2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dummy | 0,336 | 0,336 | 0,000 | 0,336 | 0,336 | 0,000 |
| k-NN | 0,923 | 0,763 | 0,160 | 0,920 | 0,784 | 0,136 |
| drzewo | 0,957 | 0,908 | 0,048 | 0,929 | 0,816 | 0,113 |
| RF | 0,962 | 0,955 | 0,008 | 0,942 | 0,802 | 0,140 |

### Ważność grup cech (RF)

| Grupa | cechy (wszystkie) | perm. wszystkie | perm. bez Idle * | perm. bez skrótów | Gini wszystkie | Gini bez Idle * | Gini bez skrótów |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Idle * (przeciek czasu) | 4 | 0,496 ± 0,068 | – | – | 0,276 | – | – |
| rozmiarowe | 22 | 0,218 ± 0,062 | 0,086 ± 0,025 | 0,236 ± 0,081 | 0,182 | 0,210 | 0,306 |
| TCP i protokół | 10 | 0,156 ± 0,081 | 0,255 ± 0,069 | 0,025 ± 0,003 | 0,313 | 0,439 | 0,110 |
| czasowe (IAT, Duration) | 15 | 0,095 ± 0,040 | 0,194 ± 0,056 | 0,285 ± 0,055 | 0,164 | 0,282 | 0,437 |
| tempo (B/s, pakiety/s) | 5 | 0,005 ± 0,013 | 0,007 ± 0,013 | -0,023 ± 0,020 | 0,055 | 0,053 | 0,098 |
| liczności | 6 | 0,000 ± 0,000 | 0,007 ± 0,010 | 0,002 ± 0,002 | 0,010 | 0,015 | 0,049 |
