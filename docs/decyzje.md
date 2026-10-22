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

## Do sprawdzenia w eksperymentach

- `FWD Init Win Bytes`, `Bwd Init Win Bytes` (początkowe okno TCP) zależą od systemu operacyjnego hosta, więc mogą działać jak skrót „która kampania”. W teście kampanii (EDA) okazały się jednymi z najsilniejszych skrótów. Sprawdzić ich ważność w E4.
- `Protocol`: VoIP to w ok. 60–70% UDP, a WWW praktycznie 0%. To uczciwa cecha, ale warto zobaczyć wynik bez niej.
