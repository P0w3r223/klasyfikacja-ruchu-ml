# Źródła danych i narzędzi: ocena, zamienniki, go/no-go E6

Date: 2026-10-22
Status: accepted (decyzje autora 2026-10-22: propozycje z tabeli przyjęte, E6 no-go z warunkiem powrotu)
Author: Piotr Cząstkiewicz + Claude
Related to: docs/prompty/00_weryfikacja_zrodel.md, docs/plan_projektu.md §4.5 i §11, docs/decyzje.md (2026-10-13)

---

## Pytanie i kryteria

Czy źródła projektu to najlepszy dostępny wybór, co je zastąpi, gdy któreś zniknie, i czy opcjonalny E6 (wczesna klasyfikacja z pierwszych N pakietów) jest wykonalny.

„Lepsze źródło” oznacza:
- WWW, VoIP i wideo zebrane w jednej kampanii pomiarowej, najlepiej także przez VPN;
- cechy zgodne z CICFlowMeter albo surowe dane pakietowe;
- licencję, która pozwala użyć danych w raporcie;
- rozmiar do obróbki na PC.

Największą wartość ma zamiennik, który usuwa efekt kampanii, bo to główna słabość obecnych danych.

Strony źródeł sprawdzono 22.10.2026, jeden przebieg (agent `researcher` + weryfikacja kluczowych faktów bezpośrednio na stronach). Lista URL-i jest na końcu.

## Tabela propozycji

| Źródło | Rola w projekcie | Stan 22.10.2026 | Ryzyko | Zamiennik | Koszt podmiany | Rekomendacja |
| --- | --- | --- | --- | --- | --- | --- |
| CIC-Darknet2020, kopia Kaggle | zbiór główny (E1–E5) | dostępna, 73 325 208 B, bez zmian od 2020-09-25; licencja UNB pozwala na mirror | niskie: plik jest też w Release `data-raw-v1` | serwer UNB (formularz); BCCC-Darknet-2025 nie zastępuje (inne klasy) | brak (ten sam plik) | **zostaje** |
| CIC-Darknet2020, serwer UNB | weryfikacja sumy SHA-256 | formularz CIC zwraca „Server error. Please try again later.” | sumy nie da się teraz porównać | kopia Kaggle (rozmiar zgodny) | – | **zapas**; SHA-256 sprawdzić, gdy formularz zadziała |
| USBVPN2022 (Naas, Fesl 2023) | kandydat bez efektu kampanii | Zenodo, CC BY 4.0, 811,7 MB zip (~18 GB po rozpakowaniu), bez rejestracji; pobrany i sprawdzony (MD5 zgodne) | VoIP bez VPN: 72 przepływy z jednego dnia, z czego część to ruch infrastruktury; przez VPN cały tunel to 1–2 przepływy; brak adresów IP (brak sesji); każda klasa z innego dnia | VNAT (tylko VoIP vs wideo) | pełny: nowy ekstraktor cech, czyszczenie, EDA, nowa definicja grup (cały M2) | **zapas**, ograniczona przydatność; nie jako podmiana ani do E6 |
| VNAT (MIT LL 2022) | kandydat dla VoIP vs Video w jednej kampanii | bezpośrednie pobranie, 36 GB PCAP + 1,05 GB i 8,6 MB h5 | **brak podanej licencji**; brak WWW | USBVPN2022 | ekstrakcja cech z PCAP, nowe sesje | **zapas** (licencja niejasna) |
| CICFlowMeter (Java, UNB) | cechy do E7 | repo bez wydań, ostatnie zmiany 2021–2022, natywny jnetpcap | znane błędy (Engelen i in. 2021), trudna instalacja | `cicflowmeter` (Python, MIT, v0.5.0, 25.10.2025) | sprawdzić zgodność cech na kilku przepływach | **zamiennik `cicflowmeter` (Python) jako narzędzie podstawowe E7**, Java jako zapas |
| NFStream | cechy z pierwszych N pakietów (E6) | v6.6.0 (16.02.2026), LGPL-3.0, koło cp313 win_amd64; Npcap | cechy niezgodne z CICFlowMeter | własny skrypt (dpkt/scapy) | – | **do rozważenia** tylko przy E6 |
| CESNET-QUIC22 | perspektywa (praca inżynierska) | Zenodo, CC BY 4.0, 21 GB zip / 89 GB, 153 mln przepływów QUIC | tylko QUIC, brak VPN, inne cechy | inne zbiory CESNET przez `cesnet-datazoo` | nie dotyczy | **zostaje jako perspektywa** |
| PCAP-y ISCX VPN-nonVPN / Tor-nonTor | E6 | ten sam formularz CIC (server error); 28 GB + 22 GB | brak dostępu teraz; WWW nie jest w VPN-nonVPN jako osobne pliki | USBVPN2022 (sprawdzony, nie nadaje się), VNAT (brak licencji) | – | **E6: no-go**, patrz niżej |

## Zbiór główny: CIC-Darknet2020

**Stan i dostępność.** Strona UNB nadal opisuje zbiór i ma tę samą licencję: „You may redistribute, republish and mirror the CICDarknet2020 dataset in any form”, pod warunkiem cytowania zbioru i artykułu DIDarknet (Lashkari, Kaur, Rahali, ICCNS 2020). Link „Download the dataset” prowadzi do formularza CIC (imię, nazwisko, e-mail, organizacja, stanowisko, kraj). 22.10.2026 formularz zwracał „Server error. Please try again later.” Strona nie podaje rozmiaru pliku ani wersji CICFlowMeter.

**Kopia Kaggle** (`peterfriedrich1/cicdarknet2020-internet-traffic`): 73 325 208 B, aktualizacja 2020-09-25, licencja „Data files © Original Authors”. Rozmiar zgadza się co do bajta z plikiem w projekcie (docs/decyzje.md). Licencja UNB pozwala na mirror, więc korzystanie z kopii jest zgodne z warunkami.

**Ryzyko.** Niskie. Surowy plik jest w naszym Release `data-raw-v1`, więc zniknięcie Kaggle lub UNB nie blokuje projektu. Jedyna otwarta sprawa to porównanie SHA-256 z plikiem z UNB (formularz nie działa).

**Zamienniki.**
- Serwer UNB: ten sam plik, gdy formularz zacznie działać.
- BCCC-Darknet-2025 (York University, grupa Lashkariego) **nie jest zamiennikiem**. Łączy CIC-Darknet2020 z innym zbiorem, liczy cechy narzędziem NTLFlowLyzer i ma klasy VPN/Tor/I2P/Freenet/ZeroNet, bez podziału na usługi. Pochodzi z tych samych kampanii ISCX, więc efektu kampanii też nie usuwa.

**Czy jest lepsze źródło?** Nie znaleziono publicznego zbioru, który jednocześnie ma WWW + VoIP + wideo z jednej kampanii, cechy CICFlowMeter albo PCAP-y i jasną licencję. Najbliżej jest USBVPN2022 (następna sekcja).

**Rekomendacja: zostaje.**

## Kandydaci bez efektu kampanii

### USBVPN2022 („Encrypted VPN Dataset”, Naas i Fesl, Data in Brief 2023)

- Jedno laboratorium (Uniwersytet Południowoczeski), jeden okres, ten sam sprzęt.
- Klasy: strony WWW bez streamingu (1022 URL-e, Selenium + Chrome 104), streaming (~105 serwisów, głównie YouTube), VoIP (Google Meet, głos i obraz), e-mail, SSH.
- Każda klasa bez VPN oraz przez 6 VPN-ów: PPTP, L2TP, L2TP-IPsec, SSTP, WireGuard, OpenVPN.
- Zenodo: CC BY 4.0, `encrypted_vpn_dataset.zip` 811,7 MB, po rozpakowaniu ~18 GB; 58 977 przepływów (50 191 bez VPN, 6 861 przez VPN).
- Format: JSON z IPFIX (pmacct). Każdy przepływ ma `x_packets` z rozmiarem (`bytes`, znak = kierunek), znacznikami czasu w µs, długościami nagłówków, numerami sekwencji i flagami TCP. Adresy IP zanonimizowane.

**Na papierze** zbiór ma wszystkie trzy usługi i VPN z jednego laboratorium, czyli dokładnie to, czego brakuje w CIC-Darknet2020.

**Sprawdzenie zawartości** (22.10.2026). Archiwum pobrano do katalogu tymczasowego, poza repo; MD5 `35a4aef7…` jest zgodne z Zenodo. Przejrzano pliki `meet.json` (bez VPN i OpenVPN) oraz `streaming.json` (bez VPN).
- Układ: `Non VPN/` i `VPN/<typ>/`, w każdym `meet.json`, `streaming.json`, `non_streaming.json`, `mail.json`, `ssh.json`. Największy plik, `Non VPN/non_streaming.json`, ma 4,1 GB.
- **Dane są pakietowe.** 91–100% wpisów w `x_packets` to pojedyncze pakiety (`packets = 1`), pozostałe to 2–3 pakiety z tej samej mikrosekundy. Pojawiają się rozmiary do ~16 KB, czyli scalone segmenty (offload karty), więc rozmiary „pakietów” nie odpowiadają w pełni temu, co widzi CICFlowMeter.
- **Przepływy nie mają adresów IP**, tylko protokół i porty. Nie da się zdefiniować sesji tak jak u nas (para IP), więc podział grupowy (P2) nie jest możliwy.
- **VoIP bez VPN to 72 przepływy z jednego dnia (17.10.2022):** TCP/443 22, UDP/443 18, TCP/10443 13, GRE 3, UDP/9000 2 i inne. Najwięcej pakietów mają GRE (21 639) i UDP/9000 (10 637), a sam ruch Meet (UDP/443) tylko 3 271. W `streaming.json` (bez VPN) jest podobnie: obok TCP/UDP 443 są GRE, UDP/9000, UDP/13231 (WireGuard na MikroTiku), TCP/8291 (Winbox), TCP/10443. Pliki „Non VPN” zawierają więc ruch tuneli i zarządzania routerem, a etykiety pochodzą z pliku, nie z przepływu.
- **Przez VPN cały tunel to jeden przepływ:** `VPN/OpenVPN/meet.json` ma 2 przepływy (TCP/1194, po jednym na kierunek). Do klasyfikacji przepływów i do E6 daje to 1–2 próbki na klasę i typ VPN.
- Każda klasa pochodzi z innego dnia (Meet bez VPN 17.10, streaming bez VPN 16.10, Meet przez OpenVPN 15.09.2022). Efekt kampanii jest słabszy (ten sam sprzęt i sieć), ale nie znika.

**Koszt podmiany.** Nowy ekstraktor cech, czyszczenie ruchu infrastruktury, nowa definicja grup bez IP i powtórzenie M2. Przy ~40 użytecznych przepływach VoIP bez VPN i braku przepływów aplikacji w VPN zysk byłby mały.

**Rekomendacja: zapas o ograniczonej przydatności.** Nie jako podmiana i nie jako podstawa E6. Można go wspomnieć w raporcie jako przykład zbioru z jednej kampanii i pokazać, dlaczego nie rozwiązuje problemu (tunel = jeden przepływ, etykieta per plik).

### VNAT (MIT Lincoln Laboratory, 2022)

- Surowe PCAP-y z jednego środowiska, VPN i bez VPN; aplikacje: Vimeo, Netflix, YouTube, Zoiper (VoIP), Skype (czat), SSH, RDP, SFTP, rsync, SCP.
- Bezpośrednie pobranie bez rejestracji: `VNAT_release_1.zip` 36 GB, `VNAT_Dataframe_release_1.h5` 1,05 GB, `VNAT_Feature_Dataframe_release_1.h5` 8,6 MB.
- **Strona nie podaje licencji.** Brak WWW, więc tylko VoIP vs wideo.

**Rekomendacja: zapas** dla zadania VoIP vs Video, jeśli USBVPN2022 okaże się nieprzydatny. Przed użyciem w raporcie trzeba ustalić warunki użycia.

## Narzędzie do cech przepływów (E7)

**CICFlowMeter (Java, `ahlashkari/CICFlowMeter`).** Repozytorium bez wydań (Releases puste), ostatnie zmiany z lat 2021–2022, 12 otwartych PR-ów. Wymaga natywnej biblioteki jnetpcap i budowania przez Gradle (`gradlew execute`). Engelen, Rimmer i Joosen (IEEE SPW/WTMC 2021) opisali błędy: przepływ TCP kończy się po pierwszym FIN, RST jest ignorowany, `Active`/`Idle` były liczone źle, liczniki PSH/URG błędne. To narzędzie wyprodukowało CIC-Darknet2020, więc te same błędy siedzą w naszych danych. Warto o tym napisać w E4, bo `Idle *` jest wśród podejrzanych skrótów.

**`cicflowmeter` (Python, hieulw).** v0.5.0 z 25.10.2025, MIT, Python ≥ 3.12 (pasuje do 3.13). `cicflowmeter -f plik.pcap -c flows.csv`. Autor pisze: „This project is not maintained actively by me.” Deklaruje te same cechy co oryginał, ale nikt publicznie nie zmierzył zgodności.

**Alternatywy.**
- Poprawiona wersja Engelena (obraz Docker od osoby trzeciej): zgodna nazwami, ale z poprawionymi błędami, więc wartości `Idle`/`Active` i liczba przepływów TCP będą się różnić od Darknet.CSV.
- NTLFlowLyzer (York/BCCC): GPL-3.0, działa na Windows, ponad 300 cech, ale inne nazwy i nastawienie na TCP. Słabo pasuje do VoIP po UDP.
- NFStream: aktywnie utrzymywany, ale własny zestaw cech.

**Ryzyko dla E7.** Model uczony na cechach Java CICFlowMeter dostanie cechy z innej implementacji. Rozbieżność implementacji nałoży się na zmianę ruchu od 2016 r.

**Rekomendacja.** Podstawowo `cicflowmeter` (Python): instaluje się w naszym venv, bez Javy i jnetpcap. W etapie 06 najpierw krótki test zgodności: te same cechy z obu narzędzi na jednym PCAP-ie albo porównanie rozkładów z Darknet.CSV. Zapas: Java CICFlowMeter. **Zostaje** (z podmianą implementacji na pythonową).

## CESNET-QUIC22 (perspektywa)

Zenodo: CC BY 4.0, otwarty dostęp; `cesnet-quic22.zip` 21,0 GB, po rozpakowaniu 89 GB. 153 mln przepływów QUIC z sieci szkieletowej CESNET (31.10–27.11.2022). Etykiety `APP` i `CATEGORY` (z SNI). Cechy: statystyki przepływu, histogramy rozmiarów i odstępów, sekwencja PPI długości 30 (odstęp, kierunek, rozmiar). Istnieje nowsza wersja rekordu, a twórcy zalecają bibliotekę `cesnet-datazoo`.

Dla tego projektu: tylko QUIC, bez VPN, inne cechy, rozmiar wymaga próbkowania. **Zostaje jako perspektywa** na pracę inżynierską. Zamiennik nie jest potrzebny, bo zbiór nie należy do zakresu.

## E6: go/no-go

**Kryteria z planu.** E6 jest „go”, gdy (1) dane pakietowe da się pobrać bez nowych barier, (2) mieszczą się na PC, (3) skrypt cech da się napisać i przetestować w 1–2 sesjach.

### Wariant planowany: PCAP-y ISCX VPN-nonVPN

1. **Dostęp: nie spełnione.** Jedyną drogą jest formularz CIC, który 22.10.2026 zwraca błąd serwera. Kopii PCAP-ów na Kaggle ani HuggingFace nie znaleziono, są tylko przetworzone pochodne.
2. **Rozmiar: spełnione.** 28 GB (VPN-nonVPN), 22 GB (Tor-nonTor); da się pobrać tylko wybrane archiwa.
3. **Skrypt: wykonalny, ale z pracą przy etykietach.**
   - Nazwy plików wskazują usługę (VoIP: `facebook_audio*`, `hangouts_audio*`, `skype_audio*`, `voipbuster*`; wideo: `youtube*`, `vimeo*`, `netflix*`; wersje `vpn_*`).
   - Pliki `*_video*` (rozmowy wideo) Deep-Packet liczy jako VoIP. Nie wiadomo, jak oznaczył je CIC-Darknet2020. Pewniej przenieść etykiety, dopasowując 5-krotkę i czas do wierszy Darknet.CSV.
   - **WWW:** strona UNB wymienia przeglądanie (Firefox, Chrome) w VPN-nonVPN, ale wśród znanych nazw plików nie ma osobnych PCAP-ów z przeglądania, a CIC-Darknet2020 nie ma przepływów NonVPN×Browsing. WWW musiałoby pochodzić z Tor-nonTor, co wprowadza z powrotem efekt kampanii. Realne zadanie to VoIP vs Video wewnątrz kampanii VPN-nonVPN.

**Werdykt dla wariantu planowanego: no-go.** Pierwsze kryterium nie jest spełnione, a nawet po naprawie formularza E6 obejmie tylko VoIP vs Video.

### Wariant alternatywny: USBVPN2022

1. **Dostęp: spełnione.** Bezpośrednie pobranie z Zenodo, bez rejestracji (sprawdzone).
2. **Rozmiar: spełnione.** 812 MB zip; pliki można czytać prosto z archiwum.
3. **Skrypt: technicznie prosty, ale dane nie odpowiadają na P4.** Cechy z pierwszych N pakietów da się policzyć z `x_packets` w jednej sesji. Brakuje jednak próbek: VoIP bez VPN to ~40–70 przepływów z jednego spotkania, a w VPN każda klasa to 1–2 przepływy tunelu. Brak IP uniemożliwia podział grupowy, więc wynik byłby zawyżony jak w E1.

**Werdykt dla wariantu alternatywnego: no-go** z powodu jakości i liczności danych, nie wykonalności.

### Rekomendacja

**E6: no-go.** Pomijamy etap 07 i opisujemy w raporcie (sekcja ograniczeń / dalsze prace):
- PCAP-y ISCX są dostępne tylko przez formularz CIC, który w październiku 2026 nie działał;
- nawet z PCAP-ami E6 dotyczyłby tylko VoIP vs Video, bo WWW w tej kampanii nie ma osobnych plików;
- sprawdzony zamiennik (USBVPN2022) ma za mało przepływów aplikacji i nie ma adresów IP do podziału grupowego.

Zwolniony czas (1–2 sesje w styczniu) przechodzi na E7 i zapas przed raportem.

**Warunek powrotu.** Jeśli formularz CIC zadziała przed 15.12.2026, a etapy do 05 będą w terminie, można wrócić do E6 w wersji VoIP vs Video na PCAP-ach VPN-nonVPN (NFStream `splt_analysis`, etykiety przez dopasowanie 5-krotki i czasu do Darknet.CSV). Wtedy trzeba poprawić prompt 07, bo zmienia się zakres.

## Luki i niepewności

- Nie wiadomo, czy błąd formularza CIC jest trwały. Sprawdzić przy okazji (autor), bo od tego zależy też SHA-256.
- Nie sprawdzono, jak CIC-Darknet2020 oznaczył rozmowy wideo (`*_video*`) ani jaką wersją CICFlowMeter go policzono.
- Zgodność `cicflowmeter` (Python) z wersją Java nie jest zmierzona publicznie; sprawdzamy ją sami w etapie 06.
- Licencja VNAT nieznana.
- W USBVPN2022 przejrzano tylko `meet.json` (bez VPN, OpenVPN) i `streaming.json` (bez VPN); `non_streaming.json` (4,1 GB) i pozostałe typy VPN nie były sprawdzane.
- „Real Network Environment Dataset” (Scientific Data 2025, https://www.nature.com/articles/s41597-025-04876-2): strona była niedostępna, zbioru nie oceniono.
- Do raportu (etap 01): Wang i in., „Bias in the Shadows: Explore Shortcuts in Encrypted Network Traffic Classification”, arXiv:2601.10180 (2026). Opisuje skróty związane ze środowiskiem pomiaru na 19 publicznych zbiorach, czyli zjawisko podobne do naszego efektu kampanii.

## Źródła

- CIC-Darknet2020: https://www.unb.ca/cic/datasets/darknet2020.html; formularz http://cicresearch.ca/CICDataset/CICDarknet2020/
- Kaggle: https://www.kaggle.com/datasets/peterfriedrich1/cicdarknet2020-internet-traffic
- ISCX VPN-nonVPN 2016: https://www.unb.ca/cic/datasets/vpn.html; formularz http://cicresearch.ca/CICDataset/ISCX-VPN-NonVPN-2016/
- ISCX Tor-nonTor 2016: https://www.unb.ca/cic/datasets/tor.html
- Mapowanie nazw PCAP na etykiety (Deep-Packet): https://github.com/munhouiani/Deep-Packet/blob/master/utils.py
- BCCC-Darknet-2025: https://www.yorku.ca/research/bccc/ucs-technical/cybersecurity-datasets-cds/encrypted-traffic-dataset-bccc-darknet-2025
- USBVPN2022: https://zenodo.org/records/7301756; artykuł: https://pmc.ncbi.nlm.nih.gov/articles/PMC9925847/
- VNAT: https://www.ll.mit.edu/r-d/datasets/vpnnonvpn-network-application-traffic-dataset-vnat; https://arxiv.org/abs/2205.05628
- CICFlowMeter: https://github.com/ahlashkari/CICFlowMeter; błędy: Engelen, Rimmer, Joosen, IEEE SPW/WTMC 2021, DOI 10.1109/SPW53761.2021.00009
- `cicflowmeter` (Python): https://pypi.org/project/cicflowmeter/
- NTLFlowLyzer: https://github.com/ahlashkari/NTLFlowLyzer
- NFStream: https://pypi.org/project/nfstream/
- CESNET-QUIC22: https://zenodo.org/records/7409924
- Wang i in. 2026: https://arxiv.org/abs/2601.10180
