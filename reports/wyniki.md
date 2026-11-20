# Wyniki projektu: klasyfikacja ruchu (CIC-Darknet2020)

Date: 2026-11-20
Status: draft
Author: Piotr Cząstkiewicz + Claude
Related to: docs/decyzje.md (wpisy E1–E7), reports/wyniki_tabele.md (tabele T1–T7)

---

Jedno źródło liczb i rysunków dla raportu, prezentacji i aplikacji. Każda liczba poniżej pochodzi z tabel T1–T7 w [wyniki_tabele.md](wyniki_tabele.md), a te z plików w `reports/results/` (ścieżka przy każdej tabeli). Wszystko odtwarza `python src/make_figures_08.py`, a test `tests/test_wyniki.py` sprawdza, że każda liczba dziesiętna z tego pliku występuje w tabelach.

**Jak czytać.** Miara główna to F1 makro, średnia z foldów zewnętrznych, z podziałem po sesjach (para IP + etykieta, przerwa ≤ 5 min), chyba że napisano inaczej. Poziom zgadywania (Dummy, E2) to 0,496 (WWW vs Video), 0,519 (VoIP vs Video) i 0,336 (3 usługi). Zadania:
- **WWW vs Video** (kampania Tor-nonTor) i **VoIP vs Video** (kampania VPN-nonVPN, ruch zwykły + VPN): zadania wewnątrz jednej kampanii, główna miara;
- **3 usługi** (ruch zwykły): odniesienie, bo łączy klasy z dwóch kampanii.

## Oś opowieści: ile zostaje z wysokiego wyniku

Rysunek: `figures/slajdy/S1_os_opowiesci.png`. Random Forest, F1 makro (T1, T7):

| Zadanie | E1: podział losowy | E2: po sesjach | E2 bez skrótów | USBVPN2022 (tylko test) |
| --- | ---: | ---: | ---: | ---: |
| WWW vs Video | 0,903 | 0,896 | 0,797 | 0,469 |
| VoIP vs Video | 0,992 | 0,989 | 0,957 | 0,545 |
| 3 usługi | 0,962 | 0,955 | 0,713 | 0,108 |

- Podział losowy prawie nie zawyża wyniku RF, dopóki w cechach jest `Idle *`.
- Usunięcie przecieku daty (`Idle *`) i cech zależnych od systemu nagrywającego zabiera najwięcej w zadaniu 3 usług (−0,242).
- Na innym zbiorze wszystkie potoki spadają do poziomu zgadywania. Wysoki wynik wewnątrz CIC-Darknet2020 mierzy w dużej części warunki nagrania, nie tylko usługę.

## P2: o ile podział losowy zawyża wynik (E1, E2)

Tabela T1, rysunki `08_e1_vs_e2.png`, `09_zawyzenie_e1_e2.png`, `10_wrazliwosc_e2.png`.

- **Na wszystkich cechach** zawyżenie (E1−E2) jest wyraźne tylko dla k-NN: +0,033 (WWW vs Video), +0,025 (VoIP vs Video), +0,160 (3 usługi). RF: +0,007, +0,003, +0,008.
- **Bez `Idle *`** zawyżenie w zadaniu 3 usług rośnie dla wszystkich modeli: k-NN +0,136, drzewo +0,113, RF +0,140. „Odporność” RF na sposób podziału wynikała z `Idle *`: data nagrania jest wspólna dla klasy także między sesjami.
- **Wewnątrz kampanii** zawyżenie bez `Idle *` wynosi najwyżej +0,032 (k-NN, WWW vs Video).
- **Odpowiedź:** podział losowy zawyża wynik o 0,113–0,140 tam, gdzie klasa ma mało sesji (VoIP w zadaniu 3 usług), a wewnątrz kampanii o najwyżej 0,032. Hipoteza z planu („wyraźny spadek, szczególnie k-NN i drzewa”) potwierdza się dopiero po usunięciu przecieku.

## Skróty i P1: które cechy odróżniają usługi (E4)

Tabela T4, rysunki `13_e4_zestawy_cech.png`, `14_e4_waznosc_grup.png`.

- **`Idle *` to przeciek:** na wszystkich cechach to najważniejsza grupa w każdym zadaniu (permutacja obniża F1 RF o 0,398 / 0,329 / 0,496). Po jej usunięciu jej rolę przejmuje grupa TCP i protokół, dlatego wiarygodny jest dopiero zestaw bez wszystkich skrótów (55 cech).
- **Koszt usunięcia skrótów** (RF, E2 bez skrótów − E2 wszystkie): −0,099 (WWW vs Video), −0,032 (VoIP vs Video), −0,242 (3 usługi).
- **Odpowiedź na P1: zależy od pary usług.**
  - WWW vs Video odróżniają głównie cechy czasowe: same czasowe RF 0,777, same rozmiarowe 0,689; permutacja w modelu bez skrótów: czasowe +0,263, rozmiarowe +0,047.
  - VoIP vs Video odróżniają głównie rozmiary: rozmiarowe 0,933, czasowe 0,895; permutacja: rozmiarowe +0,355, czasowe +0,160.
  - Obie grupy razem dają więcej niż najlepsza z nich (0,797 i 0,957). Tempo (B/s, pakiety/s) prawie nic nie wnosi: czasowe + tempo 0,785 i 0,897.
- **Ranking modeli bez skrótów** zaciera się do rzędu odchylenia między foldami: WWW vs Video RF 0,797, k-NN 0,791, drzewo 0,782; VoIP vs Video RF 0,957, k-NN 0,942, drzewo 0,926.

## Efekt kampanii

Tabela T2, slajd `figures/slajdy/S2_efekt_kampanii.png`; w EDA rysunek `06_efekt_kampanii.png`.

- **Kampanię rozpoznaje się z samego wideo:** RF odróżnia wideo z kampanii Tor-nonTor od wideo z VPN-nonVPN z dokładnością zbalansowaną 0,997 na wszystkich cechach i 0,982 bez skrótów. Same rozmiary dają 0,961, same czasy 0,888. Efekt kampanii nie jest więc artefaktem przecieku daty.
- **W zadaniu 3 usług kampania podpowiada klasę.** WWW jest tylko w Tor-nonTor, więc Video z VPN-nonVPN łatwo odróżnić od WWW po kampanii. Czułość Video RF (E2): Video z VPN-nonVPN 0,997, z Tor-nonTor 0,842. Bez skrótów różnica zostaje: 0,965 vs 0,752.
- **Wniosek:** zadanie 3 usług zawyża wynik przez kampanię. Główną miarą są zadania wewnątrz jednej kampanii (zaakceptowane przez prowadzącego 21.10).

## P3: czy tunel VPN utrudnia rozpoznanie usługi (E3)

Tabela T3, rysunek `12_e3_warianty.png`, slajd `figures/slajdy/S3_e3_vpn.png`. VoIP vs Video, 3 foldy po sesjach.

- **Pozorny spadek to przeciek daty.** Na wszystkich cechach RF wytrenowany na ruchu zwykłym i testowany na VPN spada do 0,486 (zgadywanie), parami −0,500 względem modelu uczonego na VPN. Po usunięciu `Idle *` wraca do 0,971 (VPN → VPN 0,976).
- **Bez `Idle *` różnica parami RF** (zwykły → VPN minus VPN → VPN, te same foldy testowe) wynosi −0,005 (per fold −0,025 · +0,010 · −0,001); k-NN +0,006, drzewo −0,029.
- **Bez wszystkich skrótów** zwykły → VPN jest średnio wyżej (RF +0,050), ale całą przewagę daje jeden fold (+0,156), w którym VPN → VPN wypada słabo.
- **Odpowiedź:** nie znaleźliśmy spójnego spadku przy przenoszeniu modelu z ruchu zwykłego na VPN. Pytanie da się tu rozstrzygnąć tylko w wersji „czy ruch kierowany przez VPN, widziany po dekapsulacji, ma inne cechy przepływu”, bo przepływy VPN w zbiorze to ruch wewnątrz tunelu.

## E5: Audio przez model 3 usług

Tabela T5, rysunek `16_e5_audio.png`.

- Audio model 3-klasowy uznaje głównie za Video (RF: 70,7% w Tor-nonTor, 97,6% w VPN-nonVPN zwykłym, 88,5% w VPN), a prawie nigdy za VoIP (najwyżej 1,5% przepływów w każdym modelu).
- Efekt kampanii widać i tu: w Tor-nonTor RF przypisuje Audio do WWW w 29,1% przepływów, w VPN-nonVPN zwykłym w 2,4%.
- „Audio” to w tych danych głównie rozmowy głosowe (Facebook, Hangouts, Skype), a „VoIP” to tylko VoIPBuster (wpis E6, sesja 1). Wynik mówi więc, że rozmowy głosowe innych aplikacji przypominają cechami strumień wideo, a nie VoIPBuster.

## P4: ile pierwszych pakietów wystarczy (E6)

Tabela T6, rysunek `15_e6_pierwsze_pakiety.png`, slajd `figures/slajdy/S4_e6_pierwsze_pakiety.png`. VoIP vs Video w kampanii VPN-nonVPN, cechy liczone ponownie z PCAP-ów ISCX VPN-nonVPN.

- Wszystkie przepływy (5 foldów): RF przy N = 5 ma 0,975 ± 0,010, przy pełnym przepływie 0,957 ± 0,038. Różnica parami +0,019 ± 0,032 (po foldach −0,007 … +0,071), a przy N ≥ 10 mieści się w −0,004 … +0,006.
- Przepływy z ≥ 20 pakietami (3 foldy, każdy przepływ obcięty): RF przy N = 5 −0,001 ± 0,003 względem pełnego. Przy N = 10 i 20 (−0,023 ± 0,040 i −0,031 ± 0,049) traci w jednym foldzie. k-NN i drzewo nie tracą przy żadnym N.
- Pełny przepływ z PCAP-ów odtwarza wynik E4 na `flows.parquet` (RF 0,957), więc przepływy z PCAP-ów zastępują dane z Darknet.CSV.
- **Odpowiedź:** przy 5 pierwszych pakietach nie wykryliśmy różnicy względem pełnego przepływu. To brak wykrytej różnicy przy 3–5 foldach, nie dowód równoważności. Hipoteza z planu zakładała kilkanaście–kilkadziesiąt pakietów.

## E7: modele na innym zbiorze (USBVPN2022)

Tabela T7, rysunek `17_e7_usbvpn.png`, slajd `figures/slajdy/S5_e7_inny_zbior.png`; macierze pomyłek w `results/06_e7/ocena/macierze_pomylek.png`.

- 9 potoków z `models-v1` (bez skrótów), bez treningu i strojenia na USBVPN2022. Dokładność zbalansowana: 0,488–0,546 w zadaniach 2-klasowych i 0,348–0,389 w zadaniu 3 usług, czyli poziom zgadywania.
- RF: WWW vs Video 0,797 w CV → 0,469 na USBVPN2022 (klasa większości 0,484); VoIP vs Video 0,957 → 0,545 (0,495); 3 usługi 0,713 → 0,108 (0,322).
- **Wniosek:** modele uczą się warunków nagrania co najmniej tak samo jak usługi. Wynik łączy trzy czynniki, których E7 nie rozdziela: sposób nagrania, aplikacje i protokoły z 2022 r. (QUIC) oraz własny ekstraktor cech.

## Ograniczenia

- **Jeden zbiór z kampaniami związanymi z klasami.** Browsing jest tylko w Tor-nonTor, VoIP tylko w VPN-nonVPN. Każda grupa usługa × tunel to inne dni nagrań, więc różnica klas jest zawsze także różnicą sesji i dnia.
- **Klasy węższe, niż sugerują nazwy.** VoIP to tylko VoIPBuster (2 pliki źródłowe na tunel), Video obejmuje rozmowy wideo, Audio to głównie rozmowy głosowe.
- **E3** mierzy ruch wewnątrz tunelu, nie zaszyfrowany tunel. Sesje VPN i zwykłe są osobnymi nagraniami.
- **Mało sesji VoIP.** Zadanie 3 usług i E3 liczone na 3 foldach, bo jedna rozmowa ma ok. 30% przepływów VoIP w ruchu zwykłym. Rozrzut między foldami jest duży (RF bez skrótów w 3 usługach ± 0,095), a foldy nie są niezależne.
- **E6:** tylko VoIP vs Video, te same nagrania co Darknet. Populacji `wszystkie` (5 foldów) i `min20` (3 foldy) nie zestawiamy.
- **E7:** VoIP to 62 przepływy z jednego spotkania (podajemy z licznością, bez wniosków ogólnych). E7 liczono starą definicją `Fwd Act Data Pkts` (+1 przy ładunku w pierwszym pakiecie), nieprzeliczaną. Część VPN zbioru to jedno połączenie tunelu na plik, więc podajemy tylko liczności.

## Rysunki

Raport (`reports/figures/`), z `src/make_figures_08.py`:

| Plik | Treść |
| --- | --- |
| `08_e1_vs_e2.png` | E1 vs E2, wszystkie modele, foldy |
| `09_zawyzenie_e1_e2.png` | zawyżenie E1−E2 |
| `10_wrazliwosc_e2.png` | wrażliwość E2: próg sesji, para IP |
| `11_macierze_rf.png` | macierze pomyłek RF (E1, E2) |
| `12_e3_warianty.png` | E3: 4 warianty trening → test × 3 zestawy cech |
| `13_e4_zestawy_cech.png` | E4: zestawy cech |
| `14_e4_waznosc_grup.png` | E4: ważność permutacyjna grup |
| `15_e6_pierwsze_pakiety.png` | E6: F1 od liczby pierwszych pakietów |
| `16_e5_audio.png` | E5: przewidziane klasy dla Audio |
| `17_e7_usbvpn.png` | E7: CV na Darknet vs test na USBVPN2022 |

Slajdy (`reports/figures/slajdy/`, 16:9, jeden przekaz na rysunek): `S1_os_opowiesci.png`, `S2_efekt_kampanii.png`, `S3_e3_vpn.png`, `S4_e6_pierwsze_pakiety.png`, `S5_e7_inny_zbior.png`.

Rysunki 01–07 pochodzą z EDA (`notebooks/01_eda.ipynb`) i nie są odtwarzane tym skryptem.
