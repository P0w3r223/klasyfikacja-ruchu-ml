# Literatura: prace do porównań i weryfikacja pozycji z planu

Date: 2026-10-22
Status: accepted (decyzja autora 2026-10-22: lista przyjęta, poz. 6 z §11 usunięta z raportu)
Author: Piotr Cząstkiewicz + Claude
Related to: docs/prompty/01_literatura.md, docs/plan_projektu.md §2 i §11, docs/research/zrodla.md

---

## Jak czytać ten dokument

- **[S]**: liczba przeczytana w tekście, tabeli lub rysunku źródła. Wszystkie liczby [S] z sekcji „Prace do porównań” sprawdzono dwa razy, 22.10.2026: raz agent `researcher`, raz ponownie w PDF-ie lub HTML-u źródła.
- **[N]**: liczba niesprawdzona, wzięta z abstraktu, wyszukiwarki albo cytowania w innej pracy. **Nie wpisywać do raportu** bez sprawdzenia w pełnym tekście.
- Kolumna **P** wskazuje pytanie badawcze z planu (§2): P1 to cechy czasowe vs rozmiarowe, P2 podział losowy vs po sesjach, P3 wpływ VPN, P4 pierwsze N pakietów (E6 no-go, tylko perspektywa).
- Plan (`docs/plan_projektu.md`) jest eksportem z Claude Docs i go nie edytujemy. Poprawki do §11 są niżej.

## Lista zbiorcza

| # | Praca | Publikacja | Wiarygodność | P | Co z niej bierzemy |
| --- | --- | --- | --- | --- | --- |
| 1 | Draper-Gil i in. 2016 | ICISSP 2016 (SciTePress) | recenzowana konferencja | P1, P3 | Punkt odniesienia „same cechy czasowe, podział losowy” i spadek precyzji w VPN |
| 2 | Lashkari, Kaur, Rahali 2020 (DIDarknet) | ACM ICCNS 2020 | recenzowana, niska ranga; cytowanie wymagane licencją zbioru | – | Cytowanie zbioru CIC-Darknet2020 |
| 3 | Rust-Nguyen, Stamp 2022 | arXiv (praca magisterska SJSU) | preprint | P2 | Antyprzykład: ~0,92 F1 na CIC-Darknet2020 przy IP w cechach i podziale losowym |
| 4 | Wickramasinghe i in. 2025 (SoK) | IEEE S&P 2025 | najwyższa ranga | P2 | Wytyczne: bez IP/portów, bez nakładania się sesji między treningiem a testem |
| 5 | Zhao i in. 2025 (Sweet Danger) | ACM SIGCOMM 2025 | najwyższa ranga | P2 | Podział per-packet zamiast per-flow zawyża wyniki o kilkanaście–kilkadziesiąt p.p. |
| 6 | Kanon i in. 2026 (CIFS) | EJCSIT, wydawca z listy Bealla | **słaba (wydawca drapieżny)** | – | **Usunięta z raportu** (decyzja autora); zastąpiona przez [4], [5], [10], [13] |
| 7 | Rezaei, Liu 2018/2019 | arXiv; według arXiv ICDM 2019 (Industrial Conf.) | średnia | P4 | Perspektywa E6 |
| 8 | Luxemburk i in. 2023 (CESNET-QUIC22) | Data in Brief (Elsevier) | recenzowany opis danych | – | Perspektywa (praca inżynierska) |
| 9 | Shapira, Shavitt 2021 (FlowPic) | IEEE TNSM | recenzowane czasopismo | P3 | W ISCX ruch VPN klasyfikuje się *lepiej* niż zwykły; przenoszenie modelu VPN↔non-VPN |
| 10 | Arp i in. 2022 | USENIX Security 2022 | najwyższa ranga | P2, E4 | Definicja „spurious correlations”, czyli nasz efekt kampanii |
| 11 | Wang i in. 2026 (BiasSeeker) | IEEE/ACM IWQoS 2026 | recenzowana konferencja | P2, E4 | Okno TCP jako artefakt środowiska; spadek po wyzerowaniu IP/portów |
| 12 | Luxemburk, Čejka 2023 | Computer Networks 220 | recenzowane czasopismo | P1 | Bez czasów pakietów strata < 0,5% |
| 13 | Jerabek i in. 2025 | arXiv | preprint (zespół CESNET/ČVUT) | P2 | Podział losowy → rozłączny po IP: −19 p.p.; duplikaty w zbiorach |
| 14 | Pekár, Plný, Hynek 2026 | arXiv, „under review” | preprint | P1, P2 | Terminologia podziałów (Random, Temporal, Disjoint, OOD) |
| 15 | Razooqi, Pekár 2026 | arXiv, przyjęte na CNSM 2026 | recenzowana konferencja | P3 | ISCX nagrywa VPN i non-VPN w osobnych sesjach, co miesza efekt tunelu z efektem sesji |
| 16 | Holland i in. 2022 | arXiv | preprint | (a) | Liczby z ISCX nie są porównywalne, bo prace różnie przenoszą etykiety |

### Pełne cytowania

1. G. Draper-Gil, A. H. Lashkari, M. S. I. Mamun, A. A. Ghorbani, „Characterization of Encrypted and VPN Traffic using Time-related Features”, ICISSP 2016, s. 407–414. DOI 10.5220/0005740704070414. https://www.scitepress.org/Papers/2016/57407/57407.pdf
2. A. H. Lashkari, G. Kaur, A. Rahali, „DIDarknet: A Contemporary Approach to Detect and Characterize the Darknet Traffic using Deep Image Learning”, ICCNS 2020, ACM. DOI 10.1145/3442520.3442521
3. N. Rust-Nguyen, M. Stamp, „Darknet Traffic Classification and Adversarial Attacks”, arXiv:2206.06371, 2022. https://arxiv.org/abs/2206.06371
4. N. Wickramasinghe, A. Shaghaghi, G. Tsudik, S. Jha, „SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers”, IEEE S&P 2025, s. 1825–1843. DOI 10.1109/SP61157.2025.00165. https://arxiv.org/abs/2503.20093
5. Y. Zhao, G. Dettori, M. Boffa, L. Vassio, M. Mellia, „The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification”, ACM SIGCOMM 2025. DOI 10.1145/3718958.3750498. https://arxiv.org/abs/2507.16438
6. Kanon, Fahim, Sohan, „Category-Invariance-Guided Feature Selection (CIFS): Diagnosing and Mitigating the Generalization Gap in Flow-Based VPN Traffic Classification”, European Journal of Computer Science and Information Technology 14(5):46–69, 2026. DOI 10.37745/ejcsit.2013/vol14n54669
7. S. Rezaei, X. Liu, „How to Achieve High Classification Accuracy with Just a Few Labels: A Semi-supervised Approach Using Sampled Packets”, arXiv:1812.09761. https://arxiv.org/abs/1812.09761
8. J. Luxemburk, K. Hynek, T. Čejka, A. Lukačovič, P. Šiška, „CESNET-QUIC22: A large one-month QUIC network traffic dataset from backbone lines”, Data in Brief 46 (2023) 108888. DOI 10.1016/j.dib.2023.108888
9. T. Shapira, Y. Shavitt, „FlowPic: A Generic Representation for Encrypted Traffic Classification and Applications Identification”, IEEE Transactions on Network and Service Management, 2021. DOI 10.1109/TNSM.2021.3071441
10. D. Arp i in., „Dos and Don'ts of Machine Learning in Computer Security”, USENIX Security 2022, s. 3971–3988. https://www.usenix.org/system/files/sec22-arp.pdf
11. Wang, Xie, Wang, Cui, „Bias in the Shadows: Explore Shortcuts in Encrypted Network Traffic Classification”, IEEE/ACM IWQoS 2026. DOI 10.1109/IWQoS70441.2026.11661209 (sprawdzone w Crossref). https://arxiv.org/abs/2601.10180
12. J. Luxemburk, T. Čejka, „Fine-grained TLS services classification with reject option”, Computer Networks 220 (2023) 109467. DOI 10.1016/j.comnet.2022.109467. https://arxiv.org/abs/2202.11984
13. Jerabek, Luxemburk, Plný, Koumar, Pešek, Hynek, „When Simple Model Just Works: Is Network Traffic Classification in Crisis?”, arXiv:2506.08655, 2025. https://arxiv.org/abs/2506.08655
14. Pekár, Plný, Hynek, „Tutorial on Flow-Based Network Traffic Classification Using Machine Learning”, arXiv:2601.04089, 2026. https://arxiv.org/abs/2601.04089
15. Y. S. Razooqi, A. Pekár, „Matched-View Cross-Domain Evaluation of WireGuard VPN Traffic Classification Using Early-Flow Fingerprints”, arXiv:2608.30000, przyjęte na CNSM 2026. https://arxiv.org/abs/2608.30000
16. Holland, Schmitt, Mittal, Feamster, „Towards Reproducible Network Traffic Analysis”, arXiv:2203.12410, 2022. https://arxiv.org/abs/2203.12410

Inicjały autorów [6], [11], [13], [14] i [16] trzeba uzupełnić przy składaniu bibliografii raportu.

## Weryfikacja pozycji z planu (§11)

| Poz. §11 | Czy mówi to, co plan przypisuje? | Poprawka |
| --- | --- | --- |
| 1 Draper-Gil | Tak. Tab. 2 zawiera tylko cechy czasowe (duration, IAT, active/idle, fb_psec, fp_psec), bez rozmiarów pakietów. Ewaluacja to 10-fold CV (§4.2). | – |
| 2 DIDarknet | Jako cytowanie zbioru tak. Pełnego tekstu nie przeczytano (ACM 403). | Wyniki tylko [N] |
| 3 Rust-Nguyen | **Nie jako „opis zbioru”.** W §3.1 podaje 158 659 próbek, a jej tabele sumują się do ok. 141,5 tys. To preprint. | Opisu zbioru szukać w [2] i na stronie UNB; [3] cytować jako przykład przecieku |
| 4 SoK | Tak. Eksperymenty okluzji dotyczą jednak klasyfikatorów pakietowych (ET-BERT, YaTC), nie cech przepływu. | Cytować wersję IEEE S&P 2025, nie arXiv |
| 5 Sweet Danger | Tak | Dopisać SIGCOMM 2025 i DOI |
| 6 EJCSIT | **Częściowo.** Wydawca (eajournals.org) jest na liście Bealla. Zadanie to wykrywanie VPN przy wyłączonej całej kategorii aplikacji, a nie podział po sesjach. Autorzy piszą, że podziału sesyjnego nie zrobili, bo CSV ISCX nie ma IP ani czasu (Limitations). Argument „dlatego podział grupowy jest podstawowy” z tej pracy nie wynika. | Zastąpić przez [5], [13], [10] i [4] (Guideline 5); [6] usunięta z raportu |
| 7 Rezaei, Liu | Dotyczy P4 (kilka próbkowanych pakietów, QUIC UC Davis) | Tylko perspektywa E6 |
| 8 CESNET-QUIC22 | Tak | Dopisać DOI |

## Prace do porównań: warunki i liczby

### [1] Draper-Gil i in. 2016 (P1, P3)

**Warunki:**
- narzędzie ISCXFlowMeter (poprzednik CICFlowMeter);
- 23 cechy czasowe (policzone z Tab. 2; tekst nie podaje tej liczby);
- timeout przepływu 15/30/60/120 s;
- C4.5 i KNN w Weka;
- 10-fold CV, czyli podział losowy po przepływach;
- metryki: precision, recall.

Scenariusz A to najpierw VPN vs non-VPN, potem 7 kategorii osobno w każdej grupie. Scenariusz B to 14 klas naraz.

**Liczby [S]:**
- §5.1, s. 412: „The best results (average Pr) are obtained with C4.5 and 15s of ftm: 0.84 and 0.89 for the VPN and Non-VPN classifiers respectively”.
- Detekcja VPN, C4.5, 15 s: Pr 0,89 (VPN) i 0,906 (non-VPN).
- §5.2, s. 413, scenariusz B: średnie Pr ok. 0,783 (C4.5) i 0,711 (KNN).

**Uwaga:** FlowPic [9] cytuje te liczby odwrotnie (84,0% dla non-VPN, 89,0% dla VPN). Liczby z drugiej ręki trzeba sprawdzać u źródła.

### [3] Rust-Nguyen, Stamp 2022: CIC-Darknet2020, 8 klas aplikacji (P2, antyprzykład)

**Warunki:**
- cechy CICFlowMeter z CSV, bez Flow ID i Timestamp;
- **oktety Src/Dst IP dodane jako cechy** („IP information is retained”, §3.2), razem 72 cechy;
- min-max liczony na całym zbiorze;
- StratifiedKFold 5, czyli podział losowy po przepływach;
- metryki: accuracy, F1 ważone.

**Liczby [S]:**
- Tab. 12: F1 aplikacji bez SMOTE: RF 0,922, CNN 0,887, SVM 0,834.
- §5.4: RF accuracy 92,3%.
- Rys. 6 (recall RF): browsing 0,940, VoIP 0,782, video-streaming 0,760. Częste pomyłki: video→audio-streaming 0,158, VoIP→chat 0,171.

Wynik ~0,92 osiągnięto z IP w cechach, przy podziale losowym i kampanii pomieszanej z klasą. To tło dla naszego wyniku po usunięciu skrótów.

### [5] Zhao i in. 2025, Sweet Danger (P2)

**Warunki:**
- klasyfikacja na surowych bajtach pakietów;
- ISCX-VPN: VPN-binary (2), VPN-service (6), VPN-app (16);
- metryki: accuracy i macro-F1.

Podział per-flow (§4.1): „randomly put all packets from the same flow into either train, validation and test sets.”

**Liczby [S]**, VPN-app, AC/F1 w wariancie unfrozen:

| Model | per-packet (Tab. 5) | per-flow (Tab. 4) |
| --- | --- | --- |
| ET-BERT | 96,8 / 97,0 | 82,8 / 69,7 |
| YaTC | 98,5 / 98,5 | 79,1 / 65,2 |

Na TLS-120 ET-BERT ma 97,4 per-packet i 28,0 per-flow (AC, unfrozen). Według §6.1 RF na TLS-120 osiąga accuracy 98,9% z IP i 92,6% bez IP.

**Zastrzeżenie:** zjawisko jest analogiczne do naszego, ale tu chodzi o pakiety vs przepływy, a u nas o przepływy vs sesje.

### [13] Jerabek i in. 2025 (P2, k-NN)

**Warunki:** k-NN na rozmiarach, IPT i kierunkach pierwszych ≤ 30 pakietów; 12 zbiorów, 15 zadań.

**Liczby [S]:**
- Tab. VII, CIC-DoHBrw: random shuffle 98,66, disjoint split 79,61 (Δ 18,98 względem maksimum).
- Tab. III, kolumna Distance Maj.: ISCXVPN2016-T 75,71, ISCXVPN2016-A 74,19, ISCXVPN2016-E 91,58.
- §IV-A: „over 50% of samples are redundant in more than half of the datasets.”

**Wniosek dla nas:** sprawdzić duplikaty w `flows.parquet` (etap 02).

### [4] SoK, Wickramasinghe i in. 2025 (P2)

**Liczby i cytaty [S]:**
- Guideline 1: „Avoid using Strong Identification Information (SII) features such as MAC addresses, IP addresses, and protocol ports”.
- Guideline 5: „avoiding overlap between training and testing samples drawn from the same sessions”.
- ET-BERT ma accuracy 0,96, a po anonimizacji SII 0,51 (↓0,45).
- ISCXVPN2016 ma 98,9% sesji „unencrypted”. „Szyfrowane” oznacza tu tylko TLS, DTLS lub QUIC, więc tunel VPN bez TLS liczy się jako nieszyfrowany. **Nie cytować bez tego zastrzeżenia.**

### [10] Arp i in. 2022 (P2, E4)

§2.2 [S]: „P4 – Spurious Correlations. Artifacts unrelated to the security problem create shortcut patterns for separating classes”. Przykład z tekstu: model uczy się zakresu IP sieci, z której pochodzi atak. To recenzowana nazwa naszego „efektu kampanii”.

### [11] BiasSeeker, Wang i in. 2026 (P2, E4)

**Warunki:** pola pakietowe; podział 8:1:1 losowo po przepływach; ≤ 500 przepływów na klasę.

**Liczby [S]:**
- Tab. III, ISCXVPN2016, drzewo decyzyjne: Full Feature 0,9132, Zero SII 0,8590.
- §V-B3: „The KL divergence of TCP Window Size (2.36) is significantly higher than others”.

Okno TCP najsilniej zależy od środowiska pomiaru. To wspiera nasze podejrzenie wobec `Init Win Bytes` w E4.

### [9] FlowPic, Shapira, Shavitt 2021 (P3)

**Warunki:**
- PCAP-y ISCX VPN i Tor przetworzone przez autorów;
- histogram 2D rozmiar × czas, czyli obie grupy cech;
- 5 kategorii: VoIP, Video, FT, Chat, Browsing (w VPN bez Browsing);
- bloki 60 s; bloki z tej samej 5-krotki nie trafiają do treningu i testu jednocześnie, poza tym podział 90/10 losowy;
- accuracy na zbiorach zbalansowanych.

**Liczby [S]:**
- Tab. III, kategoryzacja: non-VPN 85,0, VPN 98,4, Tor 67,8.
- Tab. IV, trening na jednym typie ruchu, test na drugim:

| Klasa | non-VPN→VPN | VPN→non-VPN |
| --- | --- | --- |
| VoIP | 99,4 | 95,8 |
| Video | 98,8 | 54,0 |

Browsing non-VPN→Tor: 57,2.

**Zaskakujący wynik:** w ISCX ruch VPN klasyfikuje się *lepiej* niż zwykły. Zestawy aplikacji w VPN i non-VPN są różne (Tab. I), więc część tej „przewagi” może wynikać ze składu danych. Podział chroni tylko przed tą samą 5-krotką, nie przed tym samym nagraniem, więc wyniki leżą między podziałem losowym a grupowym.

### [15] Razooqi, Pekár 2026 (P3)

§II [S] o ISCX-VPN-2016 i VNAT: „Both collect non-VPN and VPN traffic in separate sessions”. Dlatego spadek przy przenoszeniu modelu „conflates the encapsulation effect with these session-level differences”.

Tab. I [S]: WireGuard, te same przepływy przed tunelem i po nim, trening na non-VPN, test na VPN. Balanced accuracy:
- RF na 21 statystykach przepływu: 0,8427;
- XGBoost: 0,9271;
- CNN1D na sekwencjach: 0,9753.

**Dla nas:** nasze E3 (vpn vs plain z różnych sesji) mierzy VPN razem z różnicą sesji. To trafia do sekcji ograniczeń.

### [12] Luxemburk, Čejka 2023 (P1)

**Liczby [S]:**
- §6.4: „Not using packet times and packet directions has less than 0.5%” (negatywny wpływ na accuracy).
- Bazowa accuracy 97,41% (Tab. 2).
- Według SHAP (§6.5) rozmiary pakietów są najważniejszym wejściem.

**Zastrzeżenie:** TLS i sekwencje pakietów, nie statystyki CICFlowMeter.

### [6] EJCSIT 2026 (usunięta z raportu; zapis tylko dla porządku)

**Liczby [S]:**
- Abstrakt podaje spadek RF z 92,3% do 35–67%. W tabelach jest 92,2% (Tab. 3) i 35,0–66,6% (Tab. 4).
- Bez cech czasowych accuracy przy standardowej ewaluacji spada z 92,0% do 83,7%. Zbiór ma tylko cechy czasowe i przepływność.

Słaby wydawca, więc decyzją autora z 22.10.2026 praca nie trafia do raportu.

### [14] i [16]: kontekst bez liczb do porównań

- [14] Pekár i in.: rozmiary pakietów są „highly discriminative”, czasy „highly sensitive to network conditions” (§III-F); definicje podziałów Random, Temporal, Disjoint i OOD (§IV-D1).
- [16] Holland i in., Tab. 3 [S]: prace na ISCX VPN używają 12–31 klas i różnie przenoszą etykiety. Zeng i in. piszą: „Some files such as "Facebook_video.pcap" can be labeled as either "Browser" or "Streaming"”. Liczby z ISCX nie są więc wprost porównywalne. To ta sama niepewność co etykiety `*_video*` w zrodla.md.

## Pokrycie pytań badawczych

| Pytanie | Prace z liczbami [S] | Stan |
| --- | --- | --- |
| P1: czas vs rozmiar | [1] (same czasy: Pr 0,84 / 0,89), [12] (bez czasów < 0,5% straty), [14] jakościowo | ≥ 2 spełnione. **Luka:** brak recenzowanej ablacji „grupa czasowa vs rozmiarowa” na cechach CICFlowMeter dla usług. To argument za oryginalnością P1. |
| P2: losowy vs grupowy | [5] (per-packet→per-flow), [13] (losowy→po IP, −19 p.p.), [11], [4] (0,96→0,51), [10]; [3] jako antyprzykład | ≥ 2 spełnione. **Luka:** brak pracy z podziałem po sesjach na CIC-Darknet2020. |
| P3: VPN | [1] (VPN 0,84 vs non-VPN 0,89), [9] (VPN 98,4 vs non-VPN 85,0, Tab. IV), [15] (zastrzeżenie o sesjach) | ≥ 2 spełnione. Literatura podaje **sprzeczne kierunki**, a [15] wyjaśnia dlaczego. |
| P4 | [7], [13] | E6 no-go, tylko perspektywa |

## Liczby niesprawdzone [N]: nie wpisywać do raportu bez weryfikacji

- DIDarknet [2]: 86% (abstrakt), 94% darknet vs benign (tylko przez [3]). Podział danych i liczba cech są nieznane. Pełny tekst przez bibliotekę PWr (ACM DL).
- Wang i in. 2017 („End-to-end encrypted traffic classification with 1D-CNN”, IEEE ISI 2017): 83,0 / 98,6, tylko przez [9].
- Arp i in. [10]: odsetek prac z data snooping (~57%) i spurious correlations (~20%), odczytany z małego wykresu.
- D'hooge i in., DIMVA 2022 (sam port docelowy daje 70–100%); Lim i in., CoNEXT 2010; Yu i in., arXiv:2610.17961 (+32–33 p.p. przy nakładaniu się Src IP); Marim i in., ISWA 2023 (> 99%); Sarwar i in. (F1 0,89); Rezaei, Liu (98%).
- Koumar, Hynek, Čejka, arXiv:2307.13434: zgłoszone na CNSM 2023, publikacji nie potwierdzono.

## Wnioski dla dalszych etapów

- **E4:** według wyników wyszukiwarki [N] prace na CIC-Darknet2020 (Marim i in. 2023 i inne) wskazują jako najważniejsze `Idle Max`, `Fwd Seg Size Min`, `Bwd Init Win Bytes`, `Bwd Packet Length Min`. To pokrywa się z naszą listą podejrzanych skrótów. Razem z [11] (okno TCP) i błędami CICFlowMeter (Engelen i in. 2021, zrodla.md) daje to mocne uzasadnienie wariantu bez nich. Liczby Marim i in. trzeba sprawdzić w pełnym tekście.
- **Etap 02:** sprawdzić duplikaty przepływów w `flows.parquet` (por. [13]).
- **Raport, dyskusja:** porównywać się z [3] (~0,92 F1, podział losowy, z IP) i pokazać, ile zostaje po usunięciu skrótów i podziale po sesjach. Zaznaczyć, że wyniki z ISCX różnią się etykietami i podziałami [16], więc nie są wprost porównywalne.
