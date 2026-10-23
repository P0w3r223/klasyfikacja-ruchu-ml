# Dziennik decyzji i ustaleń

## 2026-10-13: Źródło danych

- **Plik:** `Darknet.CSV`, 73 325 208 B, SHA-256 `3E89B9747841C44401FDCEEEA18B0FD3932F7A38F53D15A47395872CBAC18433`
- **Skąd:** kopia na Kaggle `peterfriedrich1/cicdarknet2020-internet-traffic` (wgrana 2020-09-25). Oficjalne źródło (UNB, http://cicresearch.ca/CICDataset/CICDarknet2020/) wymaga formularza rejestracyjnego. Rozmiar zgadza się z plikiem z serwera UNB (73,33 MB).
- **Licencja:** UNB pozwala na redystrybucję w dowolnej formie pod warunkiem cytowania: Lashkari, Kaur, Rahali, *DIDarknet…*, ICCNS 2020.
- **Kopia w projekcie:** GitHub Release `data-raw-v1`.
- **TODO:** porównać SHA-256 z plikiem pobranym z UNB (formularz wypełnia autor; 22.10.2026 formularz zwracał błąd serwera).

## 2026-10-13: Wstępny przegląd (`src/inspect_raw.py`)

- Wiersz 328 jest uszkodzony: dwa ucięte przepływy rozdzielone ~8 MB bajtów zerowych. Pomijamy go. Zostaje **141 530 przepływów**, tyle samo co w literaturze.
- Dwie kolumny nazywają się `Label`. Pierwsza to typ ruchu (Tor / Non-Tor / VPN / NonVPN), druga usługa.
- Etykiety usług mają niespójną pisownię: `Video-Streaming` / `Video-streaming`, `Audio-Streaming` / `AUDIO-STREAMING`, `File-Transfer` / `File-transfer`. Trzeba je ujednolicić.
- 49 wierszy z inf, 47 z NaN, 15 kolumn stałych (m.in. wszystkie `Active *`), 24 457 pełnych duplikatów i 38 361 duplikatów po usunięciu IP, portów i czasu.

### Liczności w zakresie projektu (po ujednoliceniu etykiet)

| Typ ruchu | Browsing | VOIP | Video-Streaming |
| --- | ---: | ---: | ---: |
| NonVPN | **0** | 2 101 | 5 039 |
| VPN | **0** | 1 167 | 1 144 |
| Non-Tor | 32 545 | **0** | 3 382 |

### Problem: Browsing i VoIP nie występują w tej samej kampanii pomiarowej

- **Browsing** jest tylko w ruchu Non-Tor (kampania ISCX Tor-nonTor: sieć 10.152.x przez bramę Whonix, lipiec 2015 i luty 2016).
- **VoIP** jest tylko w ruchu VPN / NonVPN (kampania ISCX VPN-nonVPN: sieć 131.202.x lub tunel 10.8.x, marzec–czerwiec 2015).
- Skutek 1: brakuje kombinacji VPN × Browsing, więc eksperyment E3 dla trzech klas nie jest wykonalny na samym CIC-Darknet2020.
- Skutek 2: klasa WWW jest doskonale skorelowana z kampanią pomiarową (inna sieć, inny sprzęt, inne daty). Model może uczyć się rozpoznawać kampanię zamiast usługi.
- VoIP to mało sesji: 69 par IP i 18 źródłowych IP (NonVPN), 51 par i 12 IP (VPN), każda kampania z jednego dnia. To ma znaczenie dla GroupKFold.
- Wideo występuje w obu kampaniach (Non-Tor i NonVPN), więc pozwala zmierzyć, jak silny jest efekt kampanii.

**Decyzja (2026-10-13): wariant A.** Zostajemy przy CIC-Darknet2020 i opisujemy problem jako wynik projektu:

- trzy klasy (WWW, VoIP, Video) tylko w ruchu zwykłym (`tunnel = plain`: Non-Tor + NonVPN);
- E3 dla dwóch klas (VoIP vs Video): zwykły ruch kontra VPN, w obrębie kampanii VPN-nonVPN;
- nowy test kontrolny efektu kampanii: Video występuje w obu kampaniach (Non-Tor i NonVPN), więc sprawdzamy, czy model odróżnia kampanię przy tej samej usłudze;
- do skonsultowania z prowadzącym przy oddaniu M1.

*Aktualizacja: test kontrolny wykonano w EDA (sekcja niżej), a jego wynik zmienił plan na zadania wewnątrz kampanii.*

## 2026-10-13: Ruch tła w etykietach usług

Etykiety nadano całym plikom przechwyceń, więc ruch tła systemu dostał etykietę usługi. Przykłady:
- 73% przepływów „VoIP” w NonVPN to LLMNR (224.0.0.252:5355);
- ok. 29% „Browsing” to zapytania DNS;
- ok. 2/3 „Audio-Stream” to DNS.

**Decyzja:** w `src/preprocess.py` usuwamy przepływy, w których dowolny port to DNS, mDNS, LLMNR, NetBIOS, SSDP, DHCP, NTP, SNMP albo Dropbox LAN sync. Usuwamy też ruch do adresów multicast/broadcast i protokoły inne niż TCP/UDP. Porty służą tu wyłącznie do filtrowania, nie są cechami modelu. Liczby: `reports/preprocess_report.md`.

Po filtrze VoIP ma tylko **391 przepływów** (204 NonVPN, 187 VPN), ale to prawdziwe rozmowy: ok. 1,4 mln pakietów, m.in. serwery VoipBuster. Przepływów jest mało, bo CICFlowMeter kończy przepływ po 120 s, a rozmowa to kilka długich strumieni UDP. To ograniczenie trzeba opisać w raporcie. Do F1 makro wliczamy F1 dla VoIP.

## 2026-10-13: Definicja sesji (wersja 1)

**Sesja** to przepływy z tą samą nieuporządkowaną parą adresów IP i tą samą etykietą (typ ruchu, usługa), w których przerwa między kolejnymi przepływami nie przekracza **5 minut**.

- Uzasadnienie: dla progów 1/5/15/60 min liczba sesji stabilizuje się od ok. 5–15 min, a przy 1 min jedna rozmowa rozpada się na wiele sztucznych sesji.
- Wynik: 49 sesji VoIP NonVPN (największa ma 30% przepływów), 25 sesji VoIP VPN, 3285 sesji WWW.
- Przy podziale grupowym użyjemy `StratifiedGroupKFold`, żeby każda klasa (szczególnie VoIP) trafiła do każdego foldu.
- W E2 sprawdzimy wrażliwość wyników na próg (5 vs 15 min).

## 2026-10-13: EDA – efekt kampanii potwierdzony (`notebooks/01_eda.ipynb`)

- Random Forest odróżnia wideo z kampanii Tor-nonTor od wideo z kampanii VPN-nonVPN z dokładnością zbalansowaną **0,997** (podział grupowy, 5 foldów). Bez cech TCP: 0,989, same czasowe: 0,92, same rozmiarowe: 0,96.
- Najsilniejsze skróty: `Fwd Seg Size Min` (rozmiar nagłówka TCP, zależny od systemu operacyjnego), `Init Win Bytes`, `Idle *`.
- Wewnątrz kampanii Tor-nonTor WWW i wideo są do siebie bardzo podobne na poziomie przepływu.

**Propozycja (do potwierdzenia):** oprócz klasyfikacji trzech usług prowadzić dwa zadania wewnątrz jednej kampanii:
1. WWW vs wideo, kampania Tor-nonTor;
2. VoIP vs wideo, kampania VPN-nonVPN (ruch zwykły i VPN; zawiera E3).

Różnica wyników (3 klasy vs zadania wewnątrz kampanii) mierzy wkład efektu kampanii. Cechy TCP zależne od systemu (`Fwd Seg Size Min`, `Init Win Bytes`) traktujemy jako podejrzane: w E4 wariant z nimi i bez nich.

*Aktualizacja: propozycja zaakceptowana przez prowadzącego (sekcja niżej).*

## 2026-10-21: Decyzje prowadzącego i zakres dalszych prac

- M1 (wstęp) oddany, etap zamknięty.
- Prowadzący zaakceptował dwa zadania wewnątrz kampanii jako **główną miarę wiarygodności**: WWW vs Video (Tor-nonTor) oraz VoIP vs Video (VPN-nonVPN). Klasyfikacja trzech usług zostaje jako punkt odniesienia; różnica wyników mierzy wkład efektu kampanii.
- E3 w wersji dwuklasowej (VoIP vs Video, ruch zwykły kontra VPN) zaakceptowany.
- Zakres eksperymentów (decyzja autora): E1–E5 obowiązkowe, E7 w planie (przerwa świąteczna), E6 opcjonalny. E6 zaczynamy od oceny wykonalności; jeśli nie jest łatwo wykonalny, pomijamy go i opisujemy w raporcie.
- Prezentacja (decyzja autora): slajdy (ok. 7 min) + pokaz aplikacji Streamlit na przygotowanych plikach CSV (ok. 3 min), z nagraniem zapasowym.

## 2026-10-22: Weryfikacja źródeł i E6 (etap 00, `docs/research/zrodla.md`)

- **CIC-Darknet2020 z Kaggle zostaje.** Licencja UNB nadal pozwala na kopie, a rozmiar kopii zgadza się co do bajta. Formularz CIC (UNB) zwracał 22.10 „Server error”, więc SHA-256 z plikiem UNB nadal nieporównane. Serwer UNB jest zapasem.
- **Lepszego zbioru nie ma.** Nie znaleziono publicznego zbioru z WWW + VoIP + wideo z jednej kampanii, z PCAP-ami lub cechami CICFlowMeter i jasną licencją.
  - USBVPN2022 sprawdzony po pobraniu. Nie usuwa problemu: VoIP bez VPN to 72 przepływy z jednego dnia, z ruchem tuneli i routera w plikach „Non VPN”; przez VPN cały tunel to 1–2 przepływy; brak adresów IP.
  - USBVPN2022 i VNAT (bez licencji, bez WWW) to zapas.
- **E7: narzędzie do cech.** Pythonowy `cicflowmeter` (MIT, v0.5.0) zamiast nieutrzymywanego CICFlowMeter w Javie (Java jako zapas). W etapie 06 najpierw test zgodności cech z Darknet.CSV.
- **CICFlowMeter ma znane błędy** (Engelen i in. 2021): `Active`/`Idle`, kończenie przepływu TCP po pierwszym FIN, PSH/URG. Dotyczą też Darknet.CSV, więc warto o nich wspomnieć w E4, bo `Idle *` jest wśród podejrzanych skrótów.
- **E6: no-go z warunkiem powrotu** (decyzja autora). Powody:
  - PCAP-y ISCX dostępne tylko przez niedziałający formularz;
  - WWW w kampanii VPN-nonVPN nie ma osobnych plików;
  - zamiennik ma za mało danych.
  
  Etap 07 pomijamy, a w raporcie E6 trafia do ograniczeń i dalszych prac. Powrót tylko wtedy, gdy formularz CIC zadziała przed 15.12.2026, a etapy do 05 będą w terminie.
- CESNET-QUIC22 zostaje perspektywą dla pracy inżynierskiej.

## 2026-10-22: Literatura (etap 01, `docs/research/literatura.md`)

- **Lista literatury przyjęta.** 16 prac, każda z oceną wiarygodności. Pytania P1–P3 mają po co najmniej 2 prace z liczbami sprawdzonymi w tekście źródła. Liczby oznaczone [N] nie trafiają do raportu bez weryfikacji.
- **Poprawki do §11 planu** (planu nie edytujemy, obowiązuje literatura.md):
  - poz. 3 (Rust-Nguyen, Stamp) nie jest opisem zbioru. Cytujemy ją jako antyprzykład: ~0,92 F1 przy IP w cechach i podziale losowym;
  - poz. 4 cytujemy w wersji IEEE S&P 2025, poz. 5 w wersji SIGCOMM 2025.
- **Poz. 6 (EJCSIT) usunięta z raportu** (decyzja autora). Wydawca jest na liście Bealla, a praca nie bada podziału po sesjach. Argument za podziałem grupowym opieramy na: Sweet Danger (SIGCOMM 2025), Jerabek i in. 2025, SoK (Guideline 5) i Arp i in. (USENIX Sec 2022).
- **Do dyskusji P3:** literatura podaje sprzeczne kierunki wpływu VPN (Draper-Gil: gorzej, FlowPic: lepiej). Razooqi i Pekár (CNSM 2026) wyjaśniają to osobnymi sesjami VPN i non-VPN w ISCX. To samo ograniczenie dotyczy naszego E3.
- **Luki = oryginalność projektu:**
  - brak pracy z podziałem po sesjach na CIC-Darknet2020;
  - brak porównania grupy cech czasowych z rozmiarową na cechach CICFlowMeter dla usług.
- **Do etapu 02:** sprawdzić duplikaty przepływów w `flows.parquet` (Jerabek i in.: w ponad połowie zbiorów ponad 50% próbek jest zbędnych).

## 2026-10-22: Weryfikacja danych (etap 02)

- **`flows.parquet` jest odtwarzalny.** `Darknet.CSV` z archiwum Release `data-raw-v1` ma ten sam SHA-256 co kopia lokalna. `src/preprocess.py` uruchomiony od zera na nowym venv (Python 3.13.2, wersje z `requirements.txt`) daje pliki **identyczne bajt w bajt** z `data-processed-v1`: `flows.parquet` (SHA-256 `9cccd872…`), `features.json` i `preprocess_report.md`. Release v2 nie jest potrzebny.
- **Testy:** `tests/test_preprocess.py`, 43 testy pytest na ręcznie zbudowanych ramkach. Pokrywają filtr ruchu tła (każdy port po obu stronach, protokół, multicast, kolejność przyczyn), adresy multicast/broadcast (w tym znane fałszywe trafienia `.255`, przypięte dla odtwarzalności v1), sesje (przerwa dokładnie 5 min = ta sama sesja, odwrócona para IP, inna etykieta, nieposortowane wejście) i czyszczenie (inf/NaN, duplikaty, konflikty etykiet). Testy nie wykazały błędu w definicji sesji.
- **Znane ograniczenie reguły broadcastu, zostawione świadomie (decyzja autora).** Reguła „adres kończy się na .255” usunęła 36 przepływów. 33 to słuszne usunięcia: Audio, UDP do `131.202.243.255:57621`, czyli broadcast podsieci /22 UNB, Spotify LAN discovery. 3 to przepływy Video TCP do zwykłych hostów (`173.194.115.255:443`, `54.145.236.255:80`), usunięte błędnie (0,05% klasy Video). Zostajemy przy v1, żeby nie zmieniać danych pod wynikami EDA. Gdyby powstał v2 z innego powodu, regułę `.255` stosujemy tylko do UDP. Niepoprawnych adresów IP i multicastu po stronie Src IP nie ma.
- **Duplikaty (wniosek z literatury).** W `flows.parquet` nie ma duplikatów o tych samych 62 cechach i tej samej etykiecie. Czyszczenie usunęło wcześniej 3043 przepływy (8,6%), w tym 2894 WWW (12,6% tej klasy), więc problem jest dużo mniejszy niż „ponad 50% zbędnych próbek” u Jerabka i in. Konflikty etykiet (identyczne cechy, różne etykiety) to 255 przepływów w 122 grupach. W zadaniach głównych (bez Audio) zostaje 163 przepływy: prawie wyłącznie WWW↔Video w Tor-nonTor oraz 1 grupa VoIP NonVPN↔VPN (istotna dla E3).
- **Środowisko:** `.venv` na stacjonarnym był skopiowany z innej maszyny (`C:\Users\Ja\...`). Odtworzony z `requirements.txt`; do pliku dopisany `pytest==9.1.1`.

## 2026-10-22: Schemat oceny modeli (etap 03a)

Projekt: @architect. Decyzje: autor.

- **Zagnieżdżona walidacja krzyżowa po sesjach.**
  - Zewnętrzna: `StratifiedGroupKFold(5)`. Każda sesja jest w teście dokładnie raz, więc ocenione są wszystkie sesje VoIP: 49 w ruchu zwykłym, 25 w VPN, 74 razem.
  - Wewnętrzna: `StratifiedGroupKFold(3)` w `GridSearchCV`, refit na F1 makro. Hiperparametry dobierane są wyłącznie na części treningowej foldu zewnętrznego.
  - Powód: VoIP ma mało sesji, a są one bardzo nierówne (w ruchu zwykłym największa sesja to 30% przepływów, 3 największe to 50%; w VPN 3 największe to 44%). Jeden hold-out 70/30 dałby jedną liczbę bez rozrzutu, a w VoIP VPN ocenę na ok. 7 sesjach.
- **Odstępstwa od planu (§5.1, §5.3):**
  - CV wewnętrzna ma 3 foldy zamiast 5, bo przy 5 foldach VoIP VPN miałby po 4 sesje na fold;
  - E1 (podział losowy) to `StratifiedKFold` 5×3 w tej samej strukturze zamiast hold-outu 70/30, więc różnica E1−E2 wynika tylko z rodzaju podziału.
- **Wyniki** w `reports/results/<eksperyment>/`:
  - F1 makro per fold (średnia, odchylenie, min, max) oraz F1 z predykcji spoza foldu (OOF) i zbiorcza macierz pomyłek;
  - diagnostyka każdego foldu: liczba sesji i przepływów każdej klasy w teście, udział największej sesji testowej;
  - pomocniczo F1 makro ważona sesjami (każda sesja waży tyle samo).
- **Ochrona przed cichym błędem:** fold testowy z mniej niż 2 sesjami którejś klasy przerywa przebieg błędem.
- **Powtórzenia:** `n_repeats=1`. Powtórzoną CV (R=3) dla zadań z VoIP włączamy po pilotażu, jeśli rozrzut między foldami okaże się duży.
- **Model bazowy:** `DummyClassifier(strategy="stratified")`. Przy `most_frequent` F1 makro jest z definicji bardzo niska i nic nie mówi.
- **Struktura kodu:**
  - `src/evaluate.py`: schemat oceny bez I/O, zamrożony od 03a;
  - `src/models.py`: potoki i siatki hiperparametrów;
  - `src/experiments.py`: rejestr zadań i eksperymentów, jedyne miejsce zmian w etapach 03b–05;
  - `src/train.py`: dane, zapis wyników, CLI.
  - Foldy definiujemy na populacji testowej, a trening to populacja treningowa minus sesje foldu testowego. To obsługuje też E3 plain→VPN na tych samych foldach VPN.

**Pilotaż** (`python src/train.py --experiment pilot_03a`, wyniki w `reports/results/pilot_03a/`, kod z commitu `66bb9b0`). Zadanie VoIP vs Video, kampania VPN-nonVPN, ruch zwykły i VPN razem, 5 foldów.

| Model | Podział losowy | Podział po sesjach | Zakres po sesjach (min–max) |
| --- | --- | --- | --- |
| Dummy | 0,515 | 0,519 | 0,50–0,53 |
| k-NN | 0,994 | 0,969 | 0,95–1,00 |
| Drzewo | 0,994 | 0,979 | 0,97–0,99 |
| RF | 0,992 | 0,989 | 0,985–0,996 |

Wartości to F1 makro, średnia z foldów.

- **Rozrzut między foldami jest mały:** odchylenie standardowe nie przekracza 0,023, także w foldzie z największą sesją VoIP. **Decyzja autora: zostajemy przy `n_repeats=1`.**
- **Pomocnicza F1 ważona sesjami:** dla drzewa spada do 0,91, więc pomyłki trafiają głównie w małe sesje.
- **Wysoki wynik to jeszcze nie wniosek:** w zadaniu jest ruch zwykły i VPN, a VoIP to głównie UDP. Wkład `Protocol` i cech TCP sprawdza E4.

## 2026-10-22: E1/E2, odpowiedź na P2 (etap 03b)

Wyniki: `reports/results/03b_tabela.md` (F1 makro per fold, F1 per klasa, accuracy, czasy), `reports/results/e1e2_*`, `e2_gap15_*`, `e2_ippair_*`, rysunki `reports/figures/08–11`. Przebieg z commitu `8a5d4b1`, odtworzenie: `python src/train.py --experiment <nazwa>`, potem `python src/make_figures_03b.py`. Dwa przebiegi dały identyczne wyniki poza czasami. Sekcja o efekcie kampanii w `03b_tabela.md` wymaga lokalnych `predictions.parquet` (poza gitem), więc odtwarza się ją na komputerze stacjonarnym. Słupki błędu na rysunku 09 są orientacyjne: foldy nie są niezależne.

**Decyzje autora:**
- Opcja D (grupowanie po samej nieuporządkowanej parze IP, bez czasu i etykiety) jako analiza wrażliwości E2, tylko RF i Dummy.
- Zadanie 3 usług liczone na **3 foldach zewnętrznych** zamiast 5. Największa sesja VoIP w ruchu zwykłym ma 30% przepływów VoIP. `StratifiedGroupKFold` wyrównuje udział przepływów, nie sesji, więc przy 5 i 4 foldach jej fold dostawał tylko tę jedną sesję VoIP, a ochrona z etapu 03a przerywała przebieg. Przy 3 foldach rozkład sesji VoIP między foldy to 20/22/7. E1 i E2 mają tę samą liczbę foldów, więc różnica E1−E2 jest porównywalna wewnątrz zadania. Schemat oceny (`evaluate.py`) bez zmian.

**F1 makro, średnia z foldów zewnętrznych** (E2 = sesje 5 min):

| Zadanie | Model | E1 losowy | E2 po sesjach | E1−E2 | E2 15 min | E2 para IP |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| WWW vs Video (Tor-nonTor) | Dummy | 0,496 | 0,496 | 0,000 | 0,496 | 0,496 |
| | k-NN | 0,841 | 0,808 | 0,033 | 0,812 | – |
| | drzewo | 0,898 | 0,892 | 0,006 | 0,891 | – |
| | RF | 0,903 | 0,896 | 0,007 | 0,898 | 0,899 |
| VoIP vs Video (VPN-nonVPN) | Dummy | 0,515 | 0,519 | −0,004 | 0,519 | 0,517 |
| | k-NN | 0,994 | 0,969 | 0,025 | 0,969 | – |
| | drzewo | 0,994 | 0,979 | 0,015 | 0,977 | – |
| | RF | 0,992 | 0,989 | 0,003 | 0,986 | 0,987 |
| 3 usługi, ruch zwykły (3 foldy) | Dummy | 0,336 | 0,336 | 0,000 | 0,336 | 0,336 |
| | k-NN | 0,923 | 0,763 | 0,160 | 0,794 | – |
| | drzewo | 0,957 | 0,908 | 0,049 | 0,913 | – |
| | RF | 0,962 | 0,955 | 0,007 | 0,935 | 0,942 |

**Odpowiedź na P2:**
- **Podział losowy wyraźnie zawyża wynik k-NN, słabiej drzewa, a dla RF różnica jest nieodróżnialna od szumu.** W zadaniach wewnątrz kampanii E1−E2 wynosi dla k-NN 0,025–0,033, dla drzewa 0,006–0,015, a dla RF 0,003–0,007, przy odchyleniu między foldami RF 0,003–0,009. Przy 5 foldach zawyżenia dla RF nie da się wykazać. Dummy nie zmienia się, więc różnice pochodzą z modeli, nie z samego podziału.
- **Najmocniej cierpi klasa z małą liczbą sesji.** W zadaniu 3 usług F1 VoIP spada z E1 do E2: k-NN 0,952 → 0,520, drzewo 0,976 → 0,843, RF 0,985 → 0,972. Rozrzut E2 jest tam duży (F1 makro k-NN 0,64–0,84 między foldami): wynik zależy od tego, do którego foldu trafi kilka dużych sesji VoIP. Hipoteza (niesprawdzona w tym etapie): k-NN i drzewo dopasowują się do konkretnych sesji, a RF uśrednia. Przy 3 foldach i kilku dużych sesjach VoIP część różnicy może też wynikać z samego przydziału sesji do foldów.
- **Definicja sesji nie zmienia wniosku w zadaniach wewnątrz kampanii.** Tam próg 15 min zmienia wyniki o ≤ 0,004 (wszystkie modele), a grupowanie po parze IP (liczone tylko dla RF i Dummy) zmienia RF o ≤ 0,003. W 3 usługach RF spada do 0,935 (15 min) i 0,942 (para IP), głównie przez F1 VoIP (0,911 i 0,930), czyli znowu przez kilka dużych grup VoIP.
- **Wkład efektu kampanii.** RF po sesjach: 3 usługi 0,955, WWW vs Video wewnątrz kampanii 0,896. F1 makro dla 2 i 3 klas nie jest wprost porównywalna, ale czułość Video jest: w zadaniu 3 usług RF rozpoznaje Video z kampanii VPN-nonVPN w 99,7%, a Video z Tor-nonTor (tej samej co WWW) w 84,2%. Tak samo drzewo (99,0% vs 84,1%) i k-NN (95,9% vs 62,0%). Zadanie 3 usług zawyża więc wynik, bo część Video da się odróżnić od WWW po kampanii, a nie po usłudze. Zadanie wewnątrz kampanii jest uczciwszą miarą.
- **Czasy** (średnia na fold, WWW vs Video): predykcja RF ok. 8 µs/przepływ, drzewo < 1 µs, k-NN ok. 95 µs. Strojenie RF ok. 11 s na fold.
- **Wniosek dla kolejnych etapów (do potwierdzenia przez autora):** E3–E5 raportujemy z podziałem po sesjach. RF jest najbardziej odporny na sposób podziału. **Zrewidowane 23.10 (wpis E4): odporność RF wynikała z `Idle *`.**

## 2026-10-23: `Idle *` to znacznik czasu przepływu (przeciek daty nagrania, etap 04)

Wykryte w E3: RF wytrenowany na ruchu zwykłym i testowany na VPN spadł do F1 makro 0,486 (poziom Dummy). Trzy cechy o największej ważności Gini (`Idle Max`, `Idle Mean`, `Idle Min`, razem 0,45) mają wartości rzędu 1,43·10¹⁵.

- **W 16 557 z 32 441 przepływów (51%) `Idle Max` to bezwzględny czas przepływu w µs od 1970 roku (UTC).** Różnica względem kolumny `ts` (czas lokalny) wynosi zawsze 3,0–4,0 h, czyli tyle, co strefa czasowa Kanady ze zmianą czasu. Pozostałe przepływy mają `Idle *` = 0 albo realne wartości (334 przepływy, 5–45 s).
- Udział przepływów ze znacznikiem czasu: od 61% (WWW) do 80% (VoIP zwykły) w każdej grupie usługa × tunel. To błąd CICFlowMeter w liczeniu `Active`/`Idle` (Engelen i in. 2021, wpis z 22.10).
- **Skutek:** model może odczytać datę i godzinę nagrania. W kampanii VPN-nonVPN mediana `Idle Max` to dla VoIP zwykłego 1,4303·10¹⁵, dla Video zwykłego 1,4277·10¹⁵, a dla VoIP VPN i Video VPN 1,4323 i 1,4325·10¹⁵. RF trenowany na ruchu zwykłym uczy się reguły „później → VoIP”, więc 574 z 1015 przepływów Video VPN uznaje za VoIP.
- **Decyzja autora:** `Idle *` traktujemy jako udowodniony przeciek, nie tylko „podejrzany skrót”. E3 liczymy dodatkowo bez `Idle *` (`bez_idle`) i bez wszystkich skrótów (`bez_skrotow`: `Idle *`, `Fwd Seg Size Min`, `FWD/Bwd Init Win Bytes`); zestawy są w `src/experiments.py`.
- **Ryzyko dla E1/E2:** usługi nagrywano w różnych dniach i godzinach, więc wyniki z 03b mogą być zawyżone przez datę także przy podziale po sesjach. Wyników 03b nie zmieniamy; E4 policzy zadania z 03b na zestawach bez `Idle *` i bez skrótów, a raport poda obie wersje.
- **Dla E4 (P1):** `feature_group` w `src/features.py` zalicza `Idle *` do cech czasowych. Wariant „tylko czasowe” z `Idle *` mierzyłby więc datę, a nie dynamikę ruchu. E4 musi to uwzględnić.

## 2026-10-23: E3, odpowiedź na P3 (etap 04)

Wyniki: `reports/results/04_e3_tabela.md` (F1 makro per fold, F1 per klasa, F1 ważone sesjami, sesje VoIP w foldach), `reports/results/e3_*`, rysunek `reports/figures/12_e3_warianty.png`. Przebieg z commitu `83ecc31` (`dirty=false`), odtworzenie: `python src/train.py --experiment <nazwa>`, potem `python src/make_figures_04.py`. Dwa przebiegi dały identyczne wyniki poza czasami.

**Decyzja autora:** wszystkie 4 warianty na **3 foldach zewnętrznych**, żeby rozrzuty były porównywalne. W ruchu zwykłym przy 5 i 4 foldach największa sesja VoIP (62 z 204 przepływów) zostaje sama w foldzie i ochrona z 03a przerywa przebieg. Sesje VoIP w foldach testowych: ruch zwykły 20/7/22, VPN 8/8/9. Wariant zwykły → VPN ma te same foldy VPN co VPN → VPN, a trening to cały ruch zwykły (test w `tests/test_train_cli.py`). Wariant mieszany to zadanie `voip_video_vpncamp` z 03b, tu na 3 foldach.

**Co mierzy E3 w tych danych:**
- Przepływy „VPN” to ruch wewnątrz tunelu (adres interfejsu 10.8.x, prawdziwe adresy docelowe, porty 443/80), nie zaszyfrowany tunel. E3 pyta więc, czy ruch kierowany przez VPN, widziany po dekapsulacji, ma inne cechy przepływu, a nie czy da się sklasyfikować sam tunel.
- Każda grupa usługa × tunel to osobne dni nagrań: Video zwykłe 30.03–1.04.2015, VoIP zwykły 29.04, VoIP VPN 22.05, Video VPN 24.05. Różnica „VPN vs zwykły” to zawsze także różnica sesji i dnia (Razooqi i Pekár [15]).
- E3 jest dwuklasowy, bo w danych nie ma VPN × Browsing.

**F1 makro, średnia (odchylenie) z 3 foldów po sesjach:**

| Zestaw cech | Model | zwykły → zwykły | VPN → VPN | zwykły → VPN | mieszany |
| --- | --- | ---: | ---: | ---: | ---: |
| wszystkie | k-NN | 0,786 (0,202) | 0,972 (0,020) | 0,972 (0,022) | 0,966 (0,026) |
| | drzewo | 0,965 (0,028) | 0,962 (0,025) | 0,838 (0,024) | 0,983 (0,014) |
| | RF | 0,976 (0,031) | 0,985 (0,010) | **0,486** (0,061) | 0,991 (0,007) |
| bez `Idle *` | k-NN | 0,792 (0,194) | 0,971 (0,018) | 0,977 (0,021) | 0,975 (0,033) |
| | drzewo | 0,765 (0,181) | 0,951 (0,028) | 0,922 (0,011) | 0,944 (0,016) |
| | RF | 0,813 (0,236) | 0,976 (0,001) | 0,971 (0,018) | 0,977 (0,015) |
| bez skrótów | k-NN | 0,751 (0,164) | 0,955 (0,012) | 0,936 (0,018) | 0,915 (0,022) |
| | drzewo | 0,752 (0,180) | 0,822 (0,213) | 0,893 (0,007) | 0,865 (0,056) |
| | RF | 0,791 (0,236) | 0,897 (0,111) | 0,947 (0,018) | 0,960 (0,016) |

Dummy: 0,487–0,500 we wszystkich wariantach.

**Odpowiedź na P3:**
- **Nie znaleźliśmy dowodu, że tunel VPN utrudnia rozpoznanie VoIP vs Video.** Bez `Idle *` RF osiąga w VPN → VPN 0,976, a model wytrenowany na ruchu zwykłym i testowany na VPN 0,971. Różnica 0,005 mieści się w rozrzucie między foldami (0,001–0,018). k-NN: 0,971 vs 0,977, drzewo: 0,951 vs 0,922. Bez wszystkich skrótów zwykły → VPN jest wręcz wyżej niż VPN → VPN (RF 0,947 vs 0,897), ale VPN → VPN ma tam duży rozrzut (0,770–0,976) przy 8–9 sesjach VoIP na fold.
- **Pozorny spadek przy przenoszeniu modelu to przeciek daty.** Na wszystkich cechach RF zwykły → VPN spada do 0,486 (poziom Dummy), a drzewo do 0,838. Model uczy się z `Idle *` reguły „później → VoIP”, a wideo VPN nagrano po VoIP zwykłym. Po usunięciu `Idle *` RF wraca do 0,971. Bez tej kontroli E3 dałby fałszywą odpowiedź „VPN bardzo utrudnia przenoszenie modelu”. k-NN jest odporny, bo po skalowaniu 4 cechy `Idle *` to 4 z 62 wymiarów.
- **Ruch zwykły jest trudniejszy od VPN, ale przez jedną sesję.** W wariancie zwykły → zwykły wynik zależy od foldu z największą sesją VoIP (62 przepływy, jedna rozmowa): bez `Idle *` RF rozpoznaje w niej 3% przepływów VoIP (pozostałe sesje VoIP 91%), a na wszystkich cechach 100%, bo rozpoznaje ją po dacie. Stąd rozrzut 0,54–0,97. F1 ważone sesjami tego nie ciągnie: RF bez `Idle *` 0,901 w ruchu zwykłym i 0,952 w VPN. To ta sama rozmowa, która w 03b wymusiła 3 foldy.
- **Porównanie z literaturą.** Draper-Gil i in. [1] (C4.5, same cechy czasowe, 10-fold CV losowo, 7 kategorii) podają gorszą precyzję w VPN (0,84 vs 0,89). FlowPic [9] (histogram rozmiar × czas, podział chroniący tylko 5-krotkę) podaje lepszy wynik w VPN (98,4 vs 85,0) i dobre przeniesienie non-VPN → VPN (VoIP 99,4, Video 98,8). Nasz wynik po usunięciu przecieku jest bliżej FlowPic: przeniesienie zwykły → VPN działa. Różnice warunków: 2 klasy zamiast 5–7, cechy CICFlowMeter, podział po sesjach. Razooqi i Pekár [15] zastrzegają, że w ISCX VPN i non-VPN to osobne sesje, więc żaden z tych wyników nie izoluje samego tunelu. Nasze dane mają to samo ograniczenie, a do tego cechy liczone są z ruchu wewnątrz tunelu.
- **Wniosek dla raportu:** pytanie P3 da się na tych danych rozstrzygnąć tylko w wersji „czy ruch przez VPN widziany od środka ma inne cechy przepływu”. Odpowiedź: w zadaniu VoIP vs Video praktycznie nie. Pytanie o sam zaszyfrowany tunel wymaga zbioru z tymi samymi przepływami przed tunelem i po nim (np. [15]) i trafia do ograniczeń.
- **Ranking modeli:** bez `Idle *` RF ≈ k-NN > drzewo w wariantach z testem na VPN. Na wszystkich cechach ranking zwykły → VPN jest odwrócony (k-NN 0,972 > drzewo 0,838 > RF 0,486). To też efekt przecieku.

## 2026-10-23: E4, odpowiedź na P1 i rewizja P2 (etap 04)

Wyniki: `reports/results/04_e4_tabela.md` (F1 makro dla zestawów cech, E1/E2 bez `Idle *`, ważność grup), `reports/results/e4_*` (w tym `importance.csv`), rysunki `reports/figures/13_e4_zestawy_cech.png` i `14_e4_waznosc_grup.png`. Przebieg z commitu `c6d9f5f` (`dirty=false`), odtworzenie: `python src/train.py --experiment <nazwa>`, potem `python src/make_figures_04_e4.py`. `e4_all_*` odtwarza E2 z 03b bit w bit (różnica F1 na każdym foldzie 0,0).

**Decyzje autora:**
- `Idle *` jest w osobnej grupie `przeciek_czasu`, a grupa „czasowe” to tylko `Flow Duration` i IAT (15 cech). W EDA (etap 02, notatnik nieprzeliczany) „czasowe” obejmowały jeszcze `Idle *`.
- Dwa warianty czasowe: `tylko_czasowe` (15 cech) i `czasowe_tempo` (plus 5 cech B/s i pakiety/s, jak cechy czasowe u Draper-Gil i in. [1]). `tylko_rozmiarowe` ma 22 cechy. Żaden zestaw E4 poza „wszystkie” nie ma `Idle *`; `bez_protocol` = `bez_idle` bez `Protocol`.
- Ważność permutacyjna: wszystkie kolumny grupy dostają jedną wspólną permutację wierszy (5 powtórzeń, spadek F1 makro na teście foldu), bo cechy w grupie są silnie skorelowane i permutacja pojedynczych cech zaniża wkład grupy. Obok Gini zsumowany w grupach. Tylko RF, podział po sesjach.
- E1/E2 przeliczone bez `Idle *` jako uzupełnienie P2; wyniki 03b bez zmian.

**F1 makro RF, podział po sesjach** (średnia ± odchylenie po foldach; foldy jak w 03b):

| Zestaw cech | WWW vs Video (Tor-nonTor) | VoIP vs Video (VPN-nonVPN) | 3 usługi (odniesienie, 3 foldy) |
| --- | ---: | ---: | ---: |
| wszystkie (62) | 0,896 ± 0,009 | 0,989 ± 0,006 | 0,955 ± 0,011 |
| bez `Idle *` (58) | 0,853 ± 0,010 | 0,983 ± 0,010 | 0,802 ± 0,124 |
| bez skrótów (55) | 0,797 ± 0,012 | 0,957 ± 0,022 | 0,713 ± 0,095 |
| bez `Idle *` i `Protocol` (57) | 0,852 ± 0,011 | 0,979 ± 0,015 | 0,798 ± 0,121 |
| tylko czasowe (15) | 0,777 ± 0,012 | 0,895 ± 0,040 | 0,643 ± 0,061 |
| czasowe + tempo (20) | 0,785 ± 0,015 | 0,897 ± 0,053 | 0,663 ± 0,062 |
| tylko rozmiarowe (22) | 0,689 ± 0,012 | 0,933 ± 0,040 | 0,715 ± 0,138 |

Dummy: 0,496 / 0,519 / 0,336. Pozostałe modele w `04_e4_tabela.md`.

**Odpowiedź na P1:**
- **Która grupa cech lepiej odróżnia usługi, zależy od pary usług.** WWW vs Video odróżniają głównie cechy czasowe: same czasowe dają RF 0,777, same rozmiarowe 0,689 (wszystkie 3 modele w tej kolejności). VoIP vs Video odróżniają głównie rozmiary: 0,933 vs 0,895 (u k-NN 0,932 vs 0,855). Ważność permutacyjna w modelu bez skrótów mówi to samo: WWW vs Video czasowe 0,263, rozmiarowe 0,047; VoIP vs Video rozmiarowe 0,355, czasowe 0,160. W zadaniu 3 usług wynik jest niejednoznaczny (rozmiarowe 0,715 vs czasowe 0,643 przy odchyleniu do 0,14; permutacja czasowe 0,285 vs rozmiarowe 0,236).
- **Żadna grupa sama nie dorównuje obu razem.** Bez skrótów RF ma 0,797 (WWW vs Video) i 0,957 (VoIP vs Video), czyli więcej niż najlepsza pojedyncza grupa (0,777 i 0,933).
- **Tempo prawie nic nie wnosi.** Dodanie 5 cech B/s i pakiety/s do czasowych zmienia RF o +0,008 / +0,002 / +0,020, a ich ważność permutacyjna wynosi od −0,04 do 0,007 (ujemna = permutacja nieco pomaga, czyli szum).
- **Ile dają skróty.** Spadek RF od „wszystkie” do „bez skrótów”: WWW vs Video 0,099 (z tego `Idle *` 0,043), VoIP vs Video 0,032 (`Idle *` 0,006), 3 usługi 0,242 (`Idle *` 0,153). Na zestawie „wszystkie” `Idle *` (4 cechy) to najważniejsza grupa we wszystkich trzech zadaniach: permutacja obniża F1 o 0,40 / 0,33 / 0,50.
- **Skróty się zastępują.** Po usunięciu `Idle *` jego rolę przejmuje grupa TCP i protokół (permutacja VoIP vs Video 0,258 → 0,393, 3 usługi 0,156 → 0,255). Dopiero po usunięciu `Fwd Seg Size Min` i `Init Win Bytes` spada ona do 0,03–0,06, a ważność przenosi się na czasowe i rozmiarowe. Raport musi więc pokazywać wynik bez wszystkich skrótów, nie tylko bez `Idle *`.
- **`Protocol` jest neutralny.** `bez_idle` → `bez_protocol` zmienia RF o ≤ 0,004 we wszystkich zadaniach (drzewo w 3 usługach −0,059, ale przy odchyleniu 0,13).
- **Czy usunięcie skrótów zmienia ranking modeli: tak, a różnice się zacierają.** Na wszystkich cechach ranking to RF > drzewo > k-NN w każdym zadaniu. Bez skrótów: WWW vs Video RF 0,797 > k-NN 0,791 > drzewo 0,782 (odchylenia ok. 0,01); VoIP vs Video RF 0,957 > k-NN 0,942 > drzewo 0,926 (odchylenia 0,02–0,04); 3 usługi k-NN 0,717 ≈ RF 0,713 > drzewo 0,698 (odchylenia ok. 0,09). Drzewo traci najwięcej (0,110 / 0,053 / 0,210), k-NN najmniej (0,017 / 0,027 / 0,046), więc przewaga drzew na pełnym zestawie wynika w dużej części ze skrótów. RF zostaje najlepszy wewnątrz kampanii, ale z przewagą rzędu odchylenia między foldami.
- **Porównanie z Draper-Gil i in. [1].** Najbliższy ich warunkom jest wariant „czasowe + tempo”: RF 0,785 (WWW vs Video) i 0,897 (VoIP vs Video), drzewo 0,768 i 0,856. Oni podają średnią precyzję C4.5 0,84 (VPN) i 0,89 (non-VPN). Liczby nie są porównywalne wprost. Różnice: narzędzie (ISCXFlowMeter vs CICFlowMeter), liczba cech (23 vs 20; u nas bez `Active *`, które są stałe, i bez `Idle *`, które są przeciekiem), timeout przepływu (u nich 15–120 s, u nas taki, jak w CSV zbioru), klasyfikatory (C4.5 i KNN w Weka vs drzewo, k-NN i RF w scikit-learn ze strojeniem), podział (10-fold CV losowo vs CV po sesjach), metryka (precyzja vs F1 makro), liczba klas (7 kategorii vs 2–3) i zbiór (ISCXVPN2016 vs CIC-Darknet2020).

**Rewizja P2 (wpis z 22.10):**
- **Wniosek „RF najbardziej odporny na sposób podziału” był artefaktem `Idle *`.** Bez `Idle *` E1−E2 w zadaniu 3 usług wynosi RF 0,140 (było 0,008), drzewo 0,113 (było 0,048), k-NN 0,136 (było 0,160). `Idle *` niesie datę nagrania, która jest wspólna dla klasy także między sesjami, więc podział po sesjach nie odcinał RF od tej informacji.
- Wewnątrz kampanii różnice bez `Idle *` są małe dla wszystkich modeli: WWW vs Video RF 0,018, drzewo 0,019, k-NN 0,032; VoIP vs Video RF 0,004, drzewo 0,030, k-NN 0,005.
- **Poprawiony wniosek:** podział losowy zawyża wynik wszystkich modeli tam, gdzie klasa ma mało sesji (3 usługi, VoIP), o 0,11–0,14. Wewnątrz kampanii zawyżenie wynosi do 0,03. Wyniki E3–E5 raportujemy z podziałem po sesjach i bez skrótów. Wniosek z 22.10 zostaje w dzienniku jako zrewidowany.

## Do sprawdzenia w eksperymentach

- ~~`FWD Init Win Bytes`, `Bwd Init Win Bytes`: sprawdzić ich ważność w E4.~~ Sprawdzone 23.10 (wpis E4): po usunięciu `Idle *` grupa TCP i protokół staje się najważniejsza w VoIP vs Video, a po usunięciu `Init Win Bytes` i `Fwd Seg Size Min` jej wkład spada do 0,03–0,06.
- ~~`Protocol`: zobaczyć wynik bez niej.~~ Sprawdzone 23.10: zmiana RF ≤ 0,004.
