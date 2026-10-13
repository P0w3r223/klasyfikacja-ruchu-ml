# Dziennik decyzji i ustaleń

## 2026-10-13: Źródło danych

- **Plik:** `Darknet.CSV`, 73 325 208 B, SHA-256 `3E89B9747841C44401FDCEEEA18B0FD3932F7A38F53D15A47395872CBAC18433`
- **Skąd:** kopia na Kaggle `peterfriedrich1/cicdarknet2020-internet-traffic` (wgrana 2020-09-25). Oficjalne źródło (UNB, http://cicresearch.ca/CICDataset/CICDarknet2020/) wymaga formularza rejestracyjnego. Rozmiar zgadza się z plikiem z serwera UNB (73,33 MB).
- **Licencja:** UNB pozwala na redystrybucję w dowolnej formie pod warunkiem cytowania: Lashkari, Kaur, Rahali, *DIDarknet…*, ICCNS 2020.
- **Kopia w projekcie:** GitHub Release `data-raw-v1`.
- **TODO:** porównać SHA-256 z plikiem pobranym z UNB (formularz wypełnia autor).

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

## Do sprawdzenia w eksperymentach

- `FWD Init Win Bytes`, `Bwd Init Win Bytes` (początkowe okno TCP) zależą od systemu operacyjnego hosta, więc mogą działać jak skrót „która kampania”. Sprawdzić ich ważność w E4 i w teście kontrolnym kampanii.
- `Protocol`: VoIP to w ok. 60–70% UDP, a WWW praktycznie 0%. To uczciwa cecha, ale warto zobaczyć wynik bez niej.
