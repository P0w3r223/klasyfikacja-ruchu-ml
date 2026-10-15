# Wstęp do projektu – Klasyfikacja ruchu sieciowego z wykorzystaniem ML

Oct 13, 2026 · @Piotr

Projekt sprawdza, czy na podstawie samych statystyk przepływów (bez zaglądania w treść pakietów) można rozpoznać, czy ruch pochodzi z przeglądania WWW, rozmowy VoIP czy oglądania wideo, także w ruchu przez VPN. Wstępny przegląd danych pokazał ograniczenia zbioru, które zmieniają część zakresu. Proponowaną zmianę opisuje punkt 4.

| Pole | Wartość |
| --- | --- |
| Przedmiot | Inżynieria ruchu, Politechnika Wrocławska |
| Autor | Piotr Cząstkiewicz (telekomunikacja, V semestr) |
| Temat | Klasyfikacja ruchu sieciowego (WWW, VoIP, wideo) z wykorzystaniem uczenia maszynowego |
| Forma zaliczenia | Prezentacja 7–10 min + raport pisemny |
| Termin końcowy | Koniec stycznia 2027 |
| Repozytorium | [github.com/P0w3r223/klasyfikacja-ruchu-ml](https://github.com/P0w3r223/klasyfikacja-ruchu-ml) |

## 1. Motywacja

Operator sieci musi wiedzieć, jaki ruch przenosi, aby planować przepustowość, nadawać priorytety (QoS) i wykrywać przeciążenia. VoIP wymaga małych opóźnień i małego jittera, wideo dużej i stabilnej przepływności, a przeglądanie WWW znosi krótkie opóźnienia.

Klasyczne metody rozpoznawania ruchu przestają działać. Numery portów nie wskazują już usługi, a szyfrowanie (TLS, QUIC, VPN) uniemożliwia analizę treści pakietów (DPI). Zostaje to, co widać z zewnątrz: rozmiary pakietów, odstępy między nimi, kierunek i czas trwania przepływu.

Literatura raportuje dla takich zadań dokładności powyżej 95%, ale nowsze prace pokazują, że część tych wyników jest zawyżona przez błędy w przygotowaniu danych ([Wickramasinghe i in., 2025](https://arxiv.org/abs/2503.20093v4)). Projekt łączy więc zbudowanie klasyfikatora z krytyczną oceną, na ile jego wyniki są wiarygodne.

## 2. Cel i pytania badawcze

**Cel główny:** zbudować i porównać klasyfikatory k-NN, drzewo decyzyjne i Random Forest (wraz z modelem bazowym), które rozpoznają usługę na podstawie statystyk przepływu, i rzetelnie ocenić ich skuteczność. Efektem będzie też prosta aplikacja w Streamlit.

| ID | Pytanie badawcze | Hipoteza robocza |
| --- | --- | --- |
| P1 | Które cechy najlepiej odróżniają usługi: czasowe czy rozmiarowe? | Cechy rozmiarowe i tempo (bajty/s) odróżnią VoIP od wideo lepiej niż same odstępy czasowe. |
| P2 | O ile losowy podział danych zawyża wyniki względem podziału po sesjach? | Przy podziale po sesjach skuteczność wyraźnie spadnie, szczególnie dla k-NN i drzewa. |
| P3 | Czy tunel VPN utrudnia rozpoznanie usługi? | Skuteczność spadnie, ale nie do poziomu modelu bazowego. W zbiorze można to zbadać tylko dla VoIP i wideo (punkt 4). |
| P4 (opcjonalne) | Ile pierwszych pakietów przepływu wystarczy do rozpoznania usługi? | Kilkanaście–kilkadziesiąt pakietów da wynik zbliżony do pełnego przepływu. |

Główną miarą jest F1 makro przy podziale danych po sesjach.

## 3. Dane i wstępne ustalenia

Zbiorem głównym jest [CIC-Darknet2020](https://www.unb.ca/cic/datasets/darknet2020.html) (Canadian Institute for Cybersecurity, UNB): 141 530 przepływów z ok. 80 statystykami wyliczonymi narzędziem CICFlowMeter. Wybrałem go zamiast oryginalnych plików ISCX VPN-nonVPN 2016, bo zawiera zarówno cechy czasowe, jak i rozmiarowe, potrzebne do P1.

Przegląd danych przed modelowaniem dał trzy ustalenia ważne dla wiarygodności wyników:

1. **WWW i VoIP pochodzą z różnych kampanii pomiarowych.** Ruch WWW występuje tylko w części Tor-nonTor zbioru (inna sieć, lipiec 2015 i luty 2016). VoIP występuje tylko w części VPN-nonVPN (sieć uczelniana UNB, marzec–czerwiec 2015). W zbiorze nie ma ruchu WWW przez VPN.
2. **Etykiety obejmują ruch tła systemu.** Etykietę nadano całym plikom przechwyceń. Przez to 73% przepływów „VoIP” w ruchu bez VPN to zapytania LLMNR systemu Windows, a ok. 29% „Browsing” to zapytania DNS. Usuwam je filtrem (DNS, LLMNR, NetBIOS, SNMP, multicast i in.).
3. **VoIP ma mało przepływów.** CICFlowMeter kończy przepływ po 120 s, więc rozmowa daje kilka długich przepływów. Po czyszczeniu zostaje 391 przepływów VoIP, ale niosą one ok. 1,4 mln pakietów prawdziwych rozmów.

| Typ ruchu | WWW | VoIP | Wideo |
| --- | --- | --- | --- |
| Zwykły (Non-Tor + NonVPN) | 20 033 | 204 | 5 076 |
| VPN | 0 | 187 | 1 015 |

Liczności po odfiltrowaniu ruchu tła, błędnych wartości i duplikatów. Sesję definiuję jako przepływy między tą samą parą adresów IP z przerwami nie dłuższymi niż 5 minut. Adresy IP, porty i czas służą tylko do tej definicji i nie są cechami modelu.

## 4. Zakres projektu

Proponuję zostać przy CIC-Darknet2020 i dostosować eksperymenty do tego, co zbiór faktycznie zawiera:

- **Klasyfikacja trzech usług (WWW, VoIP, wideo)** tylko dla ruchu zwykłego.
- **Wpływ VPN (P3)** badany dla dwóch klas: VoIP i wideo. Porównanie obejmuje trening i test na ruchu zwykłym, na VPN, trening na zwykłym z testem na VPN oraz dane mieszane.
- **Nowy test kontrolny efektu kampanii.** Wideo występuje w obu kampaniach, więc sprawdzę, czy model odróżnia kampanię przy tej samej usłudze. Wstępna analiza danych już to potwierdziła: Random Forest uczony na samym wideo rozpoznaje kampanię z dokładnością zbalansowaną 0,997 (podział po sesjach), a bez cech TCP nadal 0,989. Dlatego obok klasyfikacji trzech usług prowadzę dwa zadania wewnątrz jednej kampanii: WWW vs wideo (kampania Tor-nonTor) oraz VoIP vs wideo (kampania VPN-nonVPN, także przez VPN). Różnica wyników pokaże, ile skuteczności daje sama kampania.
- **Poza zakresem:** ruch Tor (ok. 1% zbioru, inna natura ruchu), kategoria Audio-Stream (tylko jako test kontrolny), pozostałe kategorie (czat, e-mail, P2P, transfer plików).

Alternatywą jest samodzielne wyliczenie cech z surowych plików PCAP zbioru ISCX VPN-nonVPN 2016. Dałoby to spójną kampanię pomiarową, ale wymaga znacznie więcej pracy i nie wiadomo jeszcze, czy pliki zawierają ruch WWW przez VPN. Traktuję to jako kierunek na pracę inżynierską.

## 5. Metodyka i harmonogram

Każdy model oceniam dwoma schematami podziału: losowym (70/30, jak w większości publikacji) i grupowym po sesjach (StratifiedGroupKFold). Różnica między nimi odpowiada na P2. Hiperparametry dobieram 5-krotną walidacją krzyżową grupową wyłącznie na zbiorze treningowym. Skalowanie i model tworzą jeden potok scikit-learn, a nierówne liczności klas kompensują wagi klas.

Kamienie milowe:

1. **M1, 19.10.2026:** wstęp do projektu (ten dokument).
2. **M2, 16.11.2026:** oczyszczony podzbiór danych, opis zbioru (EDA), definicja sesji. Przygotowanie danych i definicja sesji w wersji 1 są już gotowe.
3. **M3, 7.12.2026:** wyniki podziału losowego i grupowego dla wszystkich modeli (P2).
4. **M4, 21.12.2026:** wpływ VPN, ważność cech, test kontrolny kampanii i Audio-Stream (P1, P3).
5. **M5, 17.01.2027:** działająca aplikacja Streamlit.
6. **M6, koniec stycznia 2027:** raport i prezentacja.

Etapy opcjonalne (wczesna klasyfikacja z PCAP, własne przechwycenia z 2026 r.) są odcinane jako pierwsze, jeśli wcześniejsze się opóźnią.

## 6. Pytania do prowadzącego

- Czy akceptuje Pan/Pani zawężenie badania wpływu VPN do dwóch klas (VoIP i wideo), wynikające z braku ruchu WWW przez VPN w zbiorze?
- Czy akceptuje Pan/Pani dodanie dwóch zadań wewnątrz jednej kampanii (WWW vs wideo, VoIP vs wideo) jako głównej miary wiarygodności obok klasyfikacji trzech usług?
- Jaka jest dokładna data oddania raportu i prezentacji?

## Literatura i źródła danych

1. A. H. Lashkari, G. Kaur, A. Rahali, [DIDarknet: A Contemporary Approach to Detect and Characterize the Darknet Traffic using Deep Image Learning](https://dl.acm.org/doi/10.1145/3442520.3442521), ICCNS 2020 (zbiór CIC-Darknet2020).
2. G. Draper-Gil, A. H. Lashkari, M. Mamun, A. A. Ghorbani, [Characterization of Encrypted and VPN Traffic Using Time-Related Features](https://www.scitepress.org/Papers/2016/57407/pdf/index.html), ICISSP 2016.
3. N. Wickramasinghe, A. Shaghaghi, G. Tsudik, S. Jha, [SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers](https://arxiv.org/abs/2503.20093v4), arXiv 2025.
4. Y. Zhao i in., [The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification](https://arxiv.org/pdf/2507.16438), 2025.
5. [Mitigating the Generalization Gap in Flow-Based VPN Traffic Classification](https://eajournals.org/ejcsit/wp-content/uploads/sites/21/2026/08/Category.pdf), EJCSIT, 2026.
6. [CIC-Darknet2020 – opis zbioru (UNB CIC)](https://www.unb.ca/cic/datasets/darknet2020.html).
