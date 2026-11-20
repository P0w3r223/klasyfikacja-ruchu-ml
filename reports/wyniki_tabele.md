# Tabele wyników (etap 08)

Wygenerowane przez `src/make_figures_08.py` z plików w `reports/results/`; nie edytować ręcznie. Średnia ± odchylenie po foldach zewnętrznych.

## T1. Tabela główna: F1 makro, zadanie × model × podział

Źródło: `reports/results/e1e2_*/, e2_gap15_*/, e2_ippair_*/folds.csv`, `reports/results/e4_*/folds.csv`. Średnia z foldów zewnętrznych; E2 = sesje 5 min; 3 usługi na 3 foldach.

| Zadanie | Model | E1 wszystkie | E2 wszystkie | E1−E2 | E1 bez Idle | E2 bez Idle | E1−E2 bez Idle | E2 bez skrótów | bez skrótów − wszystkie |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WWW vs Video | Dummy | 0,496 | 0,496 | +0,000 | 0,496 | 0,496 | +0,000 | 0,496 | +0,000 |
| WWW vs Video | k-NN | 0,841 | 0,808 | +0,033 | 0,832 | 0,800 | +0,032 | 0,791 | −0,016 |
| WWW vs Video | drzewo | 0,898 | 0,892 | +0,007 | 0,855 | 0,837 | +0,019 | 0,782 | −0,110 |
| WWW vs Video | RF | 0,903 | 0,896 | +0,007 | 0,871 | 0,853 | +0,018 | 0,797 | −0,099 |
| VoIP vs Video | Dummy | 0,515 | 0,519 | −0,005 | 0,515 | 0,519 | −0,005 | 0,519 | +0,000 |
| VoIP vs Video | k-NN | 0,994 | 0,969 | +0,025 | 0,990 | 0,985 | +0,005 | 0,942 | −0,026 |
| VoIP vs Video | drzewo | 0,994 | 0,979 | +0,014 | 0,977 | 0,947 | +0,030 | 0,926 | −0,053 |
| VoIP vs Video | RF | 0,992 | 0,989 | +0,003 | 0,987 | 0,983 | +0,004 | 0,957 | −0,032 |
| 3 usługi | Dummy | 0,336 | 0,336 | +0,000 | 0,336 | 0,336 | +0,000 | 0,336 | +0,000 |
| 3 usługi | k-NN | 0,923 | 0,763 | +0,160 | 0,920 | 0,784 | +0,136 | 0,717 | −0,047 |
| 3 usługi | drzewo | 0,957 | 0,908 | +0,048 | 0,929 | 0,816 | +0,113 | 0,698 | −0,210 |
| 3 usługi | RF | 0,962 | 0,955 | +0,008 | 0,942 | 0,802 | +0,140 | 0,713 | −0,242 |

## T2. Efekt kampanii

Źródło: `reports/results/04_kampania/folds.csv`. Wideo z ruchu zwykłego, cel = kampania, RF, 5 foldów po sesjach.

| Zestaw cech | Cech | Dokładność zbalansowana |
| --- | ---: | ---: |
| wszystkie | 62 | 0,997 ± 0,002 |
| bez Idle * | 58 | 0,996 ± 0,002 |
| bez skrótów | 55 | 0,982 ± 0,007 |
| bez Idle * i Protocol | 57 | 0,996 ± 0,003 |
| tylko czasowe | 15 | 0,888 ± 0,024 |
| czasowe + tempo | 20 | 0,895 ± 0,019 |
| tylko rozmiarowe | 22 | 0,961 ± 0,019 |

Czułość Video w zadaniu 3 usług osobno dla Video z każdej kampanii (WWW jest tylko w Tor-nonTor). Źródło: `predictions.parquet` eksperymentu (lokalnie, poza gitem) i `flows.parquet`.

| Eksperyment | Model | Podział | Video Tor-nonTor | Video VPN-nonVPN |
| --- | --- | --- | ---: | ---: |
| `e1e2_uslugi3_plain` | Dummy | E1 | 0,195 | 0,199 |
| `e1e2_uslugi3_plain` | Dummy | E2 | 0,195 | 0,199 |
| `e1e2_uslugi3_plain` | k-NN | E1 | 0,674 | 0,975 |
| `e1e2_uslugi3_plain` | k-NN | E2 | 0,620 | 0,959 |
| `e1e2_uslugi3_plain` | drzewo | E1 | 0,838 | 0,991 |
| `e1e2_uslugi3_plain` | drzewo | E2 | 0,841 | 0,990 |
| `e1e2_uslugi3_plain` | RF | E1 | 0,872 | 0,997 |
| `e1e2_uslugi3_plain` | RF | E2 | 0,842 | 0,997 |
| `e4_bez_skrotow_uslugi3_plain` | Dummy | E2 | 0,195 | 0,199 |
| `e4_bez_skrotow_uslugi3_plain` | k-NN | E2 | 0,602 | 0,850 |
| `e4_bez_skrotow_uslugi3_plain` | drzewo | E2 | 0,692 | 0,931 |
| `e4_bez_skrotow_uslugi3_plain` | RF | E2 | 0,752 | 0,965 |

## T3. E3: VoIP vs Video a tunel VPN (F1 makro, 3 foldy po sesjach)

Źródło: `reports/results/e3_*/folds.csv`.

| Zestaw cech | Model | zwykły → zwykły | VPN → VPN | zwykły → VPN | mieszany |
| --- | --- | ---: | ---: | ---: | ---: |
| wszystkie | Dummy | 0,487 ± 0,000 | 0,499 ± 0,005 | 0,500 ± 0,001 | 0,497 ± 0,000 |
| wszystkie | k-NN | 0,786 ± 0,202 | 0,972 ± 0,020 | 0,972 ± 0,022 | 0,966 ± 0,026 |
| wszystkie | drzewo | 0,965 ± 0,028 | 0,962 ± 0,025 | 0,838 ± 0,024 | 0,983 ± 0,014 |
| wszystkie | RF | 0,976 ± 0,031 | 0,985 ± 0,010 | 0,486 ± 0,061 | 0,991 ± 0,007 |
| bez Idle * | Dummy | 0,487 ± 0,000 | 0,499 ± 0,005 | 0,500 ± 0,001 | 0,497 ± 0,000 |
| bez Idle * | k-NN | 0,792 ± 0,194 | 0,971 ± 0,018 | 0,977 ± 0,021 | 0,975 ± 0,033 |
| bez Idle * | drzewo | 0,765 ± 0,181 | 0,951 ± 0,028 | 0,922 ± 0,011 | 0,944 ± 0,016 |
| bez Idle * | RF | 0,813 ± 0,236 | 0,976 ± 0,001 | 0,971 ± 0,018 | 0,977 ± 0,015 |
| bez skrótów | Dummy | 0,487 ± 0,000 | 0,499 ± 0,005 | 0,500 ± 0,001 | 0,497 ± 0,000 |
| bez skrótów | k-NN | 0,751 ± 0,164 | 0,955 ± 0,012 | 0,936 ± 0,018 | 0,915 ± 0,022 |
| bez skrótów | drzewo | 0,752 ± 0,180 | 0,822 ± 0,213 | 0,893 ± 0,007 | 0,865 ± 0,056 |
| bez skrótów | RF | 0,791 ± 0,236 | 0,897 ± 0,111 | 0,947 ± 0,018 | 0,960 ± 0,016 |

Zwykły → VPN minus VPN → VPN, parami po foldach (te same foldy testowe VPN):

| Zestaw cech | Model | per fold | średnia |
| --- | --- | ---: | ---: |
| wszystkie | k-NN | −0,001 · +0,020 · −0,020 | −0,000 |
| wszystkie | drzewo | −0,082 · −0,138 · −0,155 | −0,125 |
| wszystkie | RF | −0,433 · −0,504 · −0,562 | −0,500 |
| bez Idle * | k-NN | +0,004 · +0,035 · −0,020 | +0,006 |
| bez Idle * | drzewo | −0,030 · +0,007 · −0,063 | −0,029 |
| bez Idle * | RF | −0,025 · +0,010 · −0,001 | −0,005 |
| bez skrótów | k-NN | −0,043 · +0,015 · −0,029 | −0,019 |
| bez skrótów | drzewo | +0,316 · −0,085 · −0,019 | +0,071 |
| bez skrótów | RF | +0,156 · −0,015 · +0,009 | +0,050 |

## T4. E4: zestawy cech (F1 makro, po sesjach)

Źródło: `reports/results/e4_*/folds.csv`, `reports/results/e4_*/importance.csv`.

| Zestaw cech | Model | WWW vs Video | VoIP vs Video | 3 usługi |
| --- | --- | ---: | ---: | ---: |
| wszystkie | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| wszystkie | k-NN | 0,808 ± 0,007 | 0,969 ± 0,023 | 0,763 ± 0,106 |
| wszystkie | drzewo | 0,892 ± 0,007 | 0,979 ± 0,013 | 0,908 ± 0,060 |
| wszystkie | RF | 0,896 ± 0,009 | 0,989 ± 0,006 | 0,955 ± 0,011 |
| bez Idle * | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| bez Idle * | k-NN | 0,800 ± 0,009 | 0,985 ± 0,007 | 0,784 ± 0,135 |
| bez Idle * | drzewo | 0,837 ± 0,010 | 0,947 ± 0,038 | 0,816 ± 0,143 |
| bez Idle * | RF | 0,853 ± 0,010 | 0,983 ± 0,010 | 0,802 ± 0,124 |
| bez skrótów | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| bez skrótów | k-NN | 0,791 ± 0,007 | 0,942 ± 0,016 | 0,717 ± 0,088 |
| bez skrótów | drzewo | 0,782 ± 0,009 | 0,926 ± 0,040 | 0,698 ± 0,092 |
| bez skrótów | RF | 0,797 ± 0,012 | 0,957 ± 0,022 | 0,713 ± 0,095 |
| bez Idle * i Protocol | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| bez Idle * i Protocol | k-NN | 0,800 ± 0,009 | 0,966 ± 0,043 | 0,784 ± 0,135 |
| bez Idle * i Protocol | drzewo | 0,836 ± 0,008 | 0,947 ± 0,036 | 0,757 ± 0,131 |
| bez Idle * i Protocol | RF | 0,852 ± 0,011 | 0,979 ± 0,015 | 0,798 ± 0,121 |
| tylko czasowe | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| tylko czasowe | k-NN | 0,757 ± 0,011 | 0,855 ± 0,084 | 0,645 ± 0,054 |
| tylko czasowe | drzewo | 0,758 ± 0,013 | 0,866 ± 0,037 | 0,625 ± 0,045 |
| tylko czasowe | RF | 0,777 ± 0,012 | 0,895 ± 0,040 | 0,643 ± 0,061 |
| czasowe + tempo | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| czasowe + tempo | k-NN | 0,757 ± 0,016 | 0,800 ± 0,091 | 0,646 ± 0,055 |
| czasowe + tempo | drzewo | 0,768 ± 0,013 | 0,856 ± 0,050 | 0,645 ± 0,067 |
| czasowe + tempo | RF | 0,785 ± 0,015 | 0,897 ± 0,053 | 0,663 ± 0,062 |
| tylko rozmiarowe | Dummy | 0,496 ± 0,000 | 0,519 ± 0,012 | 0,336 ± 0,000 |
| tylko rozmiarowe | k-NN | 0,676 ± 0,022 | 0,932 ± 0,057 | 0,724 ± 0,098 |
| tylko rozmiarowe | drzewo | 0,680 ± 0,014 | 0,917 ± 0,060 | 0,644 ± 0,129 |
| tylko rozmiarowe | RF | 0,689 ± 0,012 | 0,933 ± 0,040 | 0,715 ± 0,138 |

Ważność permutacyjna grup cech (RF, spadek F1 makro po permutacji grupy):

| Zestaw cech | Grupa | WWW vs Video | VoIP vs Video | 3 usługi |
| --- | --- | ---: | ---: | ---: |
| wszystkie | czasowe | +0,057 | +0,031 | +0,095 |
| wszystkie | rozmiarowe | +0,074 | +0,008 | +0,218 |
| wszystkie | tempo | −0,016 | −0,000 | +0,005 |
| wszystkie | liczności | +0,001 | −0,000 | +0,000 |
| wszystkie | TCP i protokół | +0,023 | +0,258 | +0,156 |
| wszystkie | Idle * (przeciek) | +0,398 | +0,329 | +0,496 |
| bez skrótów | czasowe | +0,263 | +0,160 | +0,285 |
| bez skrótów | rozmiarowe | +0,047 | +0,355 | +0,236 |
| bez skrótów | tempo | −0,040 | +0,003 | −0,023 |
| bez skrótów | liczności | +0,001 | −0,001 | +0,002 |
| bez skrótów | TCP i protokół | +0,000 | +0,063 | +0,025 |

## T5. E5: Audio przez potoki 3 usług (% przepływów)

Źródło: `reports/results/05_e5/distribution.csv`.

| Model | Kampania | Tunel | Przepływy | % WWW | % VoIP | % Video |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| k-NN | tor-nontor | plain | 1321 | 52,5 | 1,0 | 46,6 |
| drzewo | tor-nontor | plain | 1321 | 36,5 | 0,4 | 63,1 |
| RF | tor-nontor | plain | 1321 | 29,1 | 0,2 | 70,7 |
| k-NN | vpn-nonvpn | plain | 1081 | 9,6 | 1,2 | 89,2 |
| drzewo | vpn-nonvpn | plain | 1081 | 4,5 | 1,5 | 94,0 |
| RF | vpn-nonvpn | plain | 1081 | 2,4 | 0,0 | 97,6 |
| k-NN | vpn-nonvpn | vpn | 3524 | 24,0 | 1,1 | 74,9 |
| drzewo | vpn-nonvpn | vpn | 3524 | 14,4 | 0,5 | 85,0 |
| RF | vpn-nonvpn | vpn | 3524 | 10,8 | 0,7 | 88,5 |

## T6. E6: VoIP vs Video z pierwszych N pakietów

Źródło: `reports/results/07_e6/ocena/summary.csv`, `reports/results/07_e6/ocena/folds.csv`. Populacji `wszystkie` (5 foldów) i `min20` (3 foldy) nie zestawiamy.

| Populacja | Model | N | F1 makro | Dokładność zbalansowana | Foldy |
| --- | --- | --- | ---: | ---: | ---: |
| wszystkie | Dummy | 5 | 0,496 ± 0,019 | 0,496 ± 0,020 | 5 |
| wszystkie | Dummy | 10 | 0,496 ± 0,019 | 0,496 ± 0,020 | 5 |
| wszystkie | Dummy | 20 | 0,496 ± 0,019 | 0,496 ± 0,020 | 5 |
| wszystkie | Dummy | 50 | 0,496 ± 0,019 | 0,496 ± 0,020 | 5 |
| wszystkie | Dummy | pełny | 0,496 ± 0,019 | 0,496 ± 0,020 | 5 |
| wszystkie | k-NN | 5 | 0,954 ± 0,034 | 0,973 ± 0,030 | 5 |
| wszystkie | k-NN | 10 | 0,945 ± 0,034 | 0,959 ± 0,039 | 5 |
| wszystkie | k-NN | 20 | 0,942 ± 0,038 | 0,955 ± 0,041 | 5 |
| wszystkie | k-NN | 50 | 0,950 ± 0,035 | 0,953 ± 0,031 | 5 |
| wszystkie | k-NN | pełny | 0,939 ± 0,018 | 0,941 ± 0,018 | 5 |
| wszystkie | drzewo | 5 | 0,952 ± 0,036 | 0,966 ± 0,021 | 5 |
| wszystkie | drzewo | 10 | 0,929 ± 0,047 | 0,948 ± 0,047 | 5 |
| wszystkie | drzewo | 20 | 0,950 ± 0,045 | 0,957 ± 0,057 | 5 |
| wszystkie | drzewo | 50 | 0,933 ± 0,040 | 0,942 ± 0,012 | 5 |
| wszystkie | drzewo | pełny | 0,930 ± 0,040 | 0,943 ± 0,036 | 5 |
| wszystkie | RF | 5 | 0,975 ± 0,010 | 0,976 ± 0,018 | 5 |
| wszystkie | RF | 10 | 0,958 ± 0,035 | 0,958 ± 0,040 | 5 |
| wszystkie | RF | 20 | 0,958 ± 0,035 | 0,960 ± 0,040 | 5 |
| wszystkie | RF | 50 | 0,959 ± 0,035 | 0,959 ± 0,037 | 5 |
| wszystkie | RF | pełny | 0,957 ± 0,038 | 0,962 ± 0,039 | 5 |
| min20 | Dummy | 5 | 0,512 ± 0,050 | 0,523 ± 0,050 | 3 |
| min20 | Dummy | 10 | 0,512 ± 0,050 | 0,523 ± 0,050 | 3 |
| min20 | Dummy | 20 | 0,512 ± 0,050 | 0,523 ± 0,050 | 3 |
| min20 | Dummy | pełny | 0,512 ± 0,050 | 0,523 ± 0,050 | 3 |
| min20 | k-NN | 5 | 0,953 ± 0,060 | 0,966 ± 0,045 | 3 |
| min20 | k-NN | 10 | 0,963 ± 0,039 | 0,972 ± 0,033 | 3 |
| min20 | k-NN | 20 | 0,967 ± 0,030 | 0,976 ± 0,027 | 3 |
| min20 | k-NN | pełny | 0,943 ± 0,045 | 0,960 ± 0,043 | 3 |
| min20 | drzewo | 5 | 0,937 ± 0,066 | 0,938 ± 0,086 | 3 |
| min20 | drzewo | 10 | 0,962 ± 0,023 | 0,969 ± 0,027 | 3 |
| min20 | drzewo | 20 | 0,959 ± 0,027 | 0,962 ± 0,033 | 3 |
| min20 | drzewo | pełny | 0,940 ± 0,041 | 0,934 ± 0,044 | 3 |
| min20 | RF | 5 | 0,967 ± 0,042 | 0,973 ± 0,035 | 3 |
| min20 | RF | 10 | 0,945 ± 0,079 | 0,937 ± 0,096 | 3 |
| min20 | RF | 20 | 0,937 ± 0,087 | 0,930 ± 0,099 | 3 |
| min20 | RF | pełny | 0,968 ± 0,039 | 0,964 ± 0,038 | 3 |

Różnica F1 makro N − pełny przepływ, parami po foldach:

| Populacja | Model | N | średnia ± odchylenie | zakres po foldach |
| --- | --- | --- | ---: | ---: |
| wszystkie | k-NN | 5 | +0,014 ± 0,028 | −0,024 … +0,053 |
| wszystkie | k-NN | 10 | +0,006 ± 0,031 | −0,041 … +0,041 |
| wszystkie | k-NN | 20 | +0,003 ± 0,030 | −0,046 … +0,034 |
| wszystkie | k-NN | 50 | +0,010 ± 0,033 | −0,036 … +0,045 |
| wszystkie | drzewo | 5 | +0,022 ± 0,050 | −0,054 … +0,084 |
| wszystkie | drzewo | 10 | −0,001 ± 0,055 | −0,079 … +0,077 |
| wszystkie | drzewo | 20 | +0,020 ± 0,045 | −0,042 … +0,084 |
| wszystkie | drzewo | 50 | +0,003 ± 0,043 | −0,027 … +0,075 |
| wszystkie | RF | 5 | +0,019 ± 0,032 | −0,007 … +0,071 |
| wszystkie | RF | 10 | +0,001 ± 0,005 | −0,004 … +0,006 |
| wszystkie | RF | 20 | +0,001 ± 0,004 | −0,004 … +0,005 |
| wszystkie | RF | 50 | +0,002 ± 0,004 | −0,004 … +0,006 |
| min20 | k-NN | 5 | +0,009 ± 0,043 | −0,023 … +0,057 |
| min20 | k-NN | 10 | +0,019 ± 0,041 | −0,018 … +0,064 |
| min20 | k-NN | 20 | +0,024 ± 0,029 | −0,006 … +0,051 |
| min20 | drzewo | 5 | −0,003 ± 0,046 | −0,048 … +0,045 |
| min20 | drzewo | 10 | +0,022 ± 0,019 | +0,000 … +0,033 |
| min20 | drzewo | 20 | +0,019 ± 0,017 | +0,000 … +0,032 |
| min20 | RF | 5 | −0,001 ± 0,003 | −0,005 … +0,001 |
| min20 | RF | 10 | −0,023 ± 0,040 | −0,070 … +0,001 |
| min20 | RF | 20 | −0,031 ± 0,049 | −0,087 … +0,000 |

## T7. E7: CIC-Darknet2020 → USBVPN2022 (tylko test)

Źródło: `reports/results/06_e7/ocena/metryki.csv`. CV = E4 bez skrótów, po sesjach. VoIP w USBVPN2022: 62 przepływy z jednego spotkania.

| Zadanie | Model | F1 makro CV | F1 makro USBVPN2022 | Dokładność zbalansowana USBVPN2022 | F1 klasy większości |
| --- | --- | ---: | ---: | ---: | ---: |
| WWW vs Video | k-NN | 0,791 ± 0,007 | 0,503 | 0,503 | 0,484 |
| WWW vs Video | drzewo | 0,782 ± 0,009 | 0,455 | 0,522 | 0,484 |
| WWW vs Video | RF | 0,797 ± 0,012 | 0,469 | 0,512 | 0,484 |
| VoIP vs Video | k-NN | 0,942 ± 0,016 | 0,487 | 0,488 | 0,495 |
| VoIP vs Video | drzewo | 0,926 ± 0,040 | 0,532 | 0,531 | 0,495 |
| VoIP vs Video | RF | 0,957 ± 0,022 | 0,545 | 0,546 | 0,495 |
| 3 usługi | k-NN | 0,717 ± 0,088 | 0,270 | 0,389 | 0,322 |
| 3 usługi | drzewo | 0,698 ± 0,092 | 0,114 | 0,348 | 0,322 |
| 3 usługi | RF | 0,713 ± 0,095 | 0,108 | 0,363 | 0,322 |
