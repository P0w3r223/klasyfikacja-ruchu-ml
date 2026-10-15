# Plan projektu: Klasyfikacja ruchu sieciowego (WWW, VoIP, wideo) z wykorzystaniem uczenia maszynowego

Oct 13, 2026 · @Piotr

Projekt sprawdza, czy na podstawie samych statystyk przepływów (bez zaglądania w treść) można rozpoznać, czy ruch pochodzi z przeglądania WWW, rozmowy VoIP czy oglądania wideo, także gdy ruch idzie przez VPN. Efektem będzie porównanie trzech klasyfikatorów, analiza wiarygodności wyników i prosta aplikacja w Streamlit.

## Metryczka

| Pole | Wartość |
| --- | --- |
| Przedmiot | Inżynieria ruchu, Politechnika Wrocławska |
| Autor | Piotr Cząstkiewicz (telekomunikacja, V semestr) |
| Temat | Klasyfikacja ruchu sieciowego (WWW, VoIP, wideo) z wykorzystaniem uczenia maszynowego |
| Status tematu | Zaakceptowany 12.10.2026 |
| Forma zaliczenia | Prezentacja 7–10 min + raport pisemny |
| Termin końcowy | Koniec stycznia 2027 (dokładna data do potwierdzenia) |
| Cel dodatkowy | Podstawa pod pracę inżynierską |

## 1. Wstęp i motywacja

Operator sieci musi wiedzieć, jaki ruch przenosi, aby planować przepustowość, nadawać priorytety (QoS) i wykrywać przeciążenia. VoIP wymaga małych opóźnień i małego jittera, wideo dużej i stabilnej przepływności, a przeglądanie WWW znosi krótkie opóźnienia.

Klasyczne metody rozpoznawania ruchu przestają działać. Numery portów nie wskazują już usługi, a szyfrowanie (TLS, QUIC, VPN) uniemożliwia analizę treści pakietów (DPI). Zostaje to, co widać z zewnątrz: rozmiary pakietów, odstępy między nimi, kierunek i czas trwania przepływu.

Uczenie maszynowe pozwala zbudować klasyfikator na tych statystykach. Literatura raportuje dla takich zadań dokładności powyżej 95%, ale nowsze prace pokazują, że część tych wyników jest zawyżona przez błędy w przygotowaniu danych. Projekt łączy więc zbudowanie klasyfikatora z krytyczną oceną, na ile jego wyniki są wiarygodne.

## 2. Cel projektu i pytania badawcze

**Cel główny:** zbudować i porównać klasyfikatory (k-NN, drzewo decyzyjne, Random Forest), które rozpoznają usługę (WWW, VoIP, wideo) na podstawie statystyk przepływu, i rzetelnie ocenić ich skuteczność.

**Cele szczegółowe:**

1. Przygotować podzbiór danych CIC-Darknet2020 wolny od cech-skrótów (adresy IP, porty, czas).
2. Wytrenować i dostroić trzy modele oraz model bazowy.
3. Odpowiedzieć na pytania badawcze P1–P4.
4. Udostępnić wyniki w aplikacji Streamlit.

| ID | Pytanie badawcze | Hipoteza robocza | Eksperymenty |
| --- | --- | --- | --- |
| P1 | Które cechy najlepiej odróżniają usługi: czasowe czy rozmiarowe? | Cechy rozmiarowe i tempo (bajty/s) odróżnią VoIP (małe, regularne pakiety) od wideo (duże pakiety, seriami) lepiej niż same odstępy czasowe. | E4 |
| P2 | O ile losowy podział danych zawyża wyniki względem podziału po sesjach? | Przy podziale po sesjach skuteczność wyraźnie spadnie, szczególnie dla k-NN i drzewa. | E1, E2 |
| P3 | Czy tunel VPN utrudnia rozpoznanie usługi? | Skuteczność spadnie, ale nie do poziomu modelu bazowego, bo VPN zachowuje rytm i przybliżone rozmiary ruchu. | E3 |
| P4 (opcjonalne) | Ile pierwszych pakietów przepływu wystarczy do rozpoznania usługi? | Kilkanaście–kilkadziesiąt pakietów da wynik zbliżony do pełnego przepływu. | E6 |

Dodatkowo eksperyment E7 sprawdzi, czy model wytrenowany na danych z 2016 r. rozpoznaje ruch przechwycony samodzielnie w 2026 r.

## 3. Zakres projektu

Projekt obejmuje klasyfikację nadzorowaną trzech usług na gotowych cechach przepływów, w dwóch wariantach ruchu: zwykłym i przez VPN. Wszystko, co wykracza poza ten rdzeń, jest opcjonalne albo przesunięte do pracy inżynierskiej.

| Element | Status | Uzasadnienie |
| --- | --- | --- |
| Klasy WWW (Browsing), VoIP, wideo (Video-Stream) | W zakresie | Usługi z tematu, o wyraźnie różnych wymaganiach QoS |
| Ruch zwykły (NonVPN) i przez VPN | W zakresie | Podstawa pytania P3 |
| k-NN, drzewo decyzyjne, Random Forest + model bazowy | W zakresie | Modele z zatwierdzonego tematu; model bazowy jako punkt odniesienia |
| Aplikacja Streamlit (wgranie CSV, wyniki) | W zakresie | Demonstracja działania |
| Wczesna klasyfikacja na podzbiorze PCAP (P4, E6) | Opcjonalnie | Wymaga własnego liczenia cech z surowych pakietów |
| Własne przechwycenia z Wiresharka (E7) | Opcjonalnie | Test na ruchu z 2026 r. |
| Ruch Tor | Poza zakresem | Uzasadnienie w punkcie 4.3 |
| Kategoria Audio-Stream | Poza zakresem (tylko test kontrolny) | Uzasadnienie w punkcie 4.3 |
| Chat, e-mail, P2P, transfer plików | Poza zakresem | Nie należą do tematu; możliwe rozszerzenie |
| Analiza treści pakietów (DPI), sieci neuronowe, klasyfikacja na żywo, wykrywanie ataków | Poza zakresem | Inny problem lub zbyt duży nakład na semestr |

## 4. Dane

Zbiorem głównym jest CIC-Darknet2020, bo zawiera ruch z ISCX VPN-nonVPN 2016 z pełnym zestawem cech czasowych i rozmiarowych. Oryginalne pliki z cechami ISCX mają tylko cechy czasowe.

### 4.1 Zbiór główny: CIC-Darknet2020

- **Pochodzenie:** połączenie zbiorów ISCX VPN-nonVPN 2016 i ISCX Tor-nonTor 2016, opracowane przez Canadian Institute for Cybersecurity (UNB) ([opis zbioru](https://www.unb.ca/cic/datasets/darknet2020.html)).
- **Cechy:** około 80 statystyk przepływu wyliczonych narzędziem CICFlowMeter: czas trwania, odstępy między pakietami (w obu kierunkach), rozmiary pakietów (min, max, średnia, odchylenie), bajty i pakiety na sekundę, flagi TCP, okresy aktywności i bezczynności.
- **Etykiety:** dwa poziomy. Typ ruchu (Tor, Non-Tor, VPN, NonVPN) oraz kategoria usługi (Audio-Stream, Browsing, Chat, Email, P2P, Transfer, Video-Stream, VOIP).
- **Wielkość:** w zależności od wersji ok. 141–159 tys. przepływów; dokładną liczbę po czyszczeniu podam w raporcie.

**Dlaczego nie oryginalne pliki CSV z ISCX VPN-nonVPN 2016?** Udostępnione cechy obejmują 23 statystyki czasowe (czas trwania, odstępy fiat/biat/flowiat, active/idle, bajty i pakiety na sekundę) i nie zawierają rozmiarów pakietów ([Draper-Gil i in., 2016](https://www.scitepress.org/Papers/2016/57407/pdf/index.html)). Pytanie P1 wymaga obu grup cech.

### 4.2 Wybrany podzbiór

Do eksperymentów trafiają przepływy o typie ruchu VPN lub NonVPN i kategorii Browsing, VOIP lub Video-Stream. Daje to sześć kombinacji, z których model przewiduje trzy klasy usług. Typ ruchu (VPN / NonVPN) nie jest celem klasyfikacji, tylko warunkiem eksperymentu E3.

Przepływy z typem Non-Tor to zwykły ruch z kampanii pomiarowej zbioru ISCX Tor-nonTor. Wstępnie traktuję je jako ruch zwykły, razem z NonVPN. Ostateczna decyzja zapadnie po eksploracji danych: sprawdzę duplikaty i zgodność rozkładów cech z NonVPN.

### 4.3 Świadome wyłączenia

Poniższe decyzje są celowe i zostaną opisane w raporcie wraz z liczbą odrzuconych przepływów.

**Ruch Tor (typ Tor).**

- Tor przesyła dane w komórkach o stałym rozmiarze, więc cechy rozmiarowe zachowują się w nim zupełnie inaczej niż w zwykłym ruchu i w VPN. Mieszanie tych danych zaciemniłoby odpowiedź na P1 i P3.
- Przepływy Tor stanowią ok. 1% zbioru, co za mało na rzetelne wnioski w podziale na trzy usługi.
- Temat dotyczy porównania ruchu zwykłego z VPN.
- Rozszerzenie o Tor (klasyfikacja hierarchiczna: najpierw typ ruchu, potem usługa) jest kierunkiem dla pracy inżynierskiej.

**Kategoria Audio-Stream.**

- Według twórców zbioru Audio-Stream i Video-Stream pochodzą z tych samych aplikacji (YouTube, Vimeo), więc granica między etykietami jest niejednoznaczna i wprowadza szum.
- Temat dotyczy wideo, nie strumieniowania dźwięku.
- **Test kontrolny (E5):** gotowy model zostanie uruchomiony na przepływach Audio-Stream. Raport pokaże, do której klasy trafiają; oczekiwanie: głównie do wideo. To zweryfikuje, czy wyłączenie było zasadne.

**Pozostałe kategorie (Chat, Email, P2P, Transfer)** nie należą do tematu. Ich dodanie to naturalne rozszerzenie.

### 4.4 Przygotowanie danych

1. **Usunięcie cech-skrótów:** Flow ID, adresy IP, porty, znacznik czasu. Model mógłby rozpoznawać po nich konkretne sesje zamiast zachowania ruchu; ten problem jest dobrze opisany w literaturze ([Wickramasinghe i in., 2025](https://arxiv.org/abs/2503.20093v4)). Adresy IP i czas posłużą wcześniej do zdefiniowania sesji na potrzeby podziału grupowego (punkt 5.1).
2. **Czyszczenie:** usunięcie duplikatów, wartości nieskończonych i pustych (typowych np. dla bajtów na sekundę przy zerowym czasie trwania) oraz cech o stałej wartości.
3. **Opis zbioru (EDA):** liczności klas w podziale VPN / NonVPN, rozkłady kluczowych cech, korelacje.
4. **Skalowanie:** standaryzacja cech wewnątrz potoku (pipeline) scikit-learn, dopasowywana tylko na danych treningowych. Jest niezbędna dla k-NN.

### 4.5 Dane dodatkowe

| Zbiór | Rola | Status |
| --- | --- | --- |
| Podzbiór PCAP z [ISCX VPN-nonVPN 2016](https://www.unb.ca/cic/datasets/vpn.html) (tylko pliki VoIP, streaming wideo, przeglądanie) | Wczesna klasyfikacja (E6): cechy z pierwszych N pakietów, N = 5, 10, 20, 50 | Opcjonalnie, styczeń |
| Własne przechwycenia (Wireshark + CICFlowMeter) | Test generalizacji (E7): rozmowa głosowa, YouTube, przeglądanie stron; z VPN, jeśli będzie dostępny | Opcjonalnie, przerwa świąteczna |
| [CESNET-QUIC22](https://zenodo.org/record/7409923) | Prawdziwy ruch z sieci szkieletowej (QUIC), sekwencje 30 pierwszych pakietów | Perspektywa, praca inżynierska |

Własne przechwycenia obejmą wyłącznie ruch z mojego komputera. Do dalszej analizy trafią tylko statystyki przepływów, bez treści pakietów.

## 5. Metodyka

Każdy model jest oceniany dwoma schematami podziału danych, a główną miarą jest F1 makro przy podziale po sesjach. Dzięki temu wyniki da się porównać z literaturą i jednocześnie pokazać, ile z nich wynika z przecieku danych.

### 5.1 Podział danych

- **Podział losowy (stratyfikowany, 70/30):** jak w większości publikacji; służy do porównania z literaturą.
- **Podział grupowy (po sesjach):** przepływy z jednej sesji (ta sama para adresów klient–serwer w zbliżonym czasie) trafiają w całości do treningu albo do testu. Dokładna definicja sesji zostanie ustalona podczas eksploracji danych. Narzędzia: GroupShuffleSplit i GroupKFold ze scikit-learn.

Praca z 2026 r. pokazała, że przy ocenie na aplikacjach niewidzianych w treningu dokładność Random Forest w wykrywaniu VPN na ISCX spadła z 92,3% do 35–67% ([EJCSIT 2026](https://eajournals.org/ejcsit/wp-content/uploads/sites/21/2026/08/Category.pdf)). Dlatego podział grupowy jest tu podstawowy.

### 5.2 Modele

| Model | Rola | Strojone hiperparametry |
| --- | --- | --- |
| Model bazowy (DummyClassifier) | Punkt odniesienia: zawsze najczęstsza klasa lub losowanie wg proporcji | brak |
| k-NN | Model oparty na odległości; wrażliwy na skalowanie | liczba sąsiadów k, metryka odległości, wagi sąsiadów |
| Drzewo decyzyjne | Model interpretowalny; reguły można pokazać na prezentacji | maksymalna głębokość, minimalna liczba próbek w liściu, kryterium podziału |
| Random Forest | Zespół drzew; zwykle najlepszy na danych tabelarycznych | liczba drzew, maksymalna głębokość, liczba cech w podziale |

Nierówne liczności klas są kompensowane wagami klas (class\_weight).

### 5.3 Strojenie i walidacja

Hiperparametry są dobierane przeszukiwaniem siatki (GridSearchCV lub RandomizedSearchCV) z 5-krotną walidacją krzyżową grupową, wyłącznie na zbiorze treningowym. Zbiór testowy jest używany raz, do końcowej oceny. Skalowanie i model tworzą jeden potok, więc dane testowe nie wpływają na trening.

### 5.4 Metryki oceny

- **F1 makro** (główna): średnia F1 z trzech klas, odporna na nierówne liczności.
- **Accuracy:** dla porównania z literaturą.
- **F1 dla każdej klasy i macierz pomyłek:** które usługi są mylone ze sobą.
- **Ważność cech:** wbudowana w Random Forest (Gini) oraz permutacyjna na zbiorze testowym; cechy pogrupowane na czasowe, rozmiarowe i tempo.
- **Czas uczenia i predykcji:** istotny dla inżynierii ruchu, bo klasyfikator miałby działać na bieżącym ruchu.

### 5.5 Plan eksperymentów

| ID | Eksperyment | Pytanie | Status |
| --- | --- | --- | --- |
| E1 | Wszystkie modele, podział losowy | P2 | Obowiązkowy |
| E2 | Wszystkie modele, podział grupowy; porównanie z E1 | P2 | Obowiązkowy |
| E3 | Wpływ VPN: trening i test na NonVPN; na VPN; trening na NonVPN i test na VPN; dane mieszane | P3 | Obowiązkowy |
| E4 | Ważność cech oraz modele uczone tylko na cechach czasowych, tylko rozmiarowych i na wszystkich | P1 | Obowiązkowy |
| E5 | Test kontrolny: klasyfikacja przepływów Audio-Stream gotowym modelem | uzasadnienie wyłączenia | Obowiązkowy (krótki) |
| E6 | Wczesna klasyfikacja: cechy z pierwszych N pakietów (podzbiór PCAP) | P4 | Opcjonalny |
| E7 | Test na własnych przechwyceniach z 2026 r. | generalizacja | Opcjonalny |

E4 z cechami tylko czasowymi odtwarza warunki oryginalnej pracy o ISCX, więc pozwala bezpośrednio sprawdzić, ile wnoszą rozmiary pakietów.

## 6. Opis działania całości

Modele są uczone raz, w skryptach i notatnikach. Gotowy potok (skalowanie + model) trafia do pliku i jest ładowany przez aplikację, więc dane w aplikacji przechodzą dokładnie te same kroki co w treningu.

&#91;embedded content: architektura projektu · uczenie i aplikacja\]

Lewa część odpowiada na pytania badawcze, prawa pokazuje działanie klasyfikatora na dowolnym pliku z przepływami.

### 6.1 Aplikacja Streamlit

1. Użytkownik wgrywa plik CSV z przepływami w formacie CICFlowMeter.
2. Aplikacja sprawdza wymagane kolumny i usuwa cechy-skróty.
3. Użytkownik wybiera model: k-NN, drzewo decyzyjne lub Random Forest.
4. Aplikacja pokazuje klasę każdego przepływu, rozkład klas i najważniejsze cechy. Jeśli plik ma etykiety, pokazuje też macierz pomyłek i F1.

### 6.2 Narzędzia

| Obszar | Narzędzie |
| --- | --- |
| Język | Python 3 |
| Przetwarzanie danych | pandas, NumPy |
| Uczenie i ocena | scikit-learn |
| Wykresy | matplotlib, seaborn |
| Zapis modeli | joblib |
| Aplikacja | Streamlit |
| Przechwytywanie i cechy | Wireshark, CICFlowMeter; dla E6 własny skrypt (np. scapy) |
| Kod i wersje | Git, GitHub |

### 6.3 Wstępna struktura repozytorium

```text
data/        surowe i przetworzone dane (poza repozytorium)
notebooks/   eksploracja danych i wykresy
src/         preprocess.py, train.py, evaluate.py, pcap_features.py
models/      zapisane potoki (.joblib)
app/         streamlit_app.py
reports/     tabele wyników i rysunki do raportu
```

## 7. Harmonogram i kamienie milowe

Wszystkie obowiązkowe eksperymenty (E1–E5) kończą się przed przerwą świąteczną. Styczeń jest przeznaczony na aplikację, raport i prezentację. Harmonogram zakłada ok. 5 godzin pracy tygodniowo.

&#91;embedded content: harmonogram · październik 2026 – styczeń 2027\]

Etapy opcjonalne (E6, E7) są odcinane jako pierwsze, jeśli wcześniejsze etapy się opóźnią.

**Kamienie milowe**

1. **M1, 19.10.2026:** wstęp do projektu oddany prowadzącemu.
2. **M2, 16.11.2026:** oczyszczony podzbiór danych, opis zbioru (EDA), ustalona definicja sesji.
3. **M3, 7.12.2026:** wyniki E1 i E2 dla wszystkich modeli; pierwsza odpowiedź na P2.
4. **M4, 21.12.2026:** wyniki E3–E5; odpowiedzi na P1 i P3.
5. **M5, 17.01.2027:** działająca aplikacja Streamlit.
6. **M6, koniec stycznia 2027:** raport i prezentacja.

## 8. Rezultaty projektu

| Rezultat | Forma |
| --- | --- |
| Kod źródłowy | Repozytorium Git (GitHub): przygotowanie danych, trening, ocena, aplikacja |
| Wytrenowane modele | Pliki potoków (joblib) gotowe do użycia w aplikacji |
| Wyniki eksperymentów E1–E5 (+ E6, E7, jeśli zostaną wykonane) | Tabele metryk, macierze pomyłek, wykresy ważności cech |
| Aplikacja | Streamlit, uruchamiana lokalnie |
| Raport | Dokument: wstęp, dane, metodyka, wyniki, dyskusja, ograniczenia, wnioski |
| Prezentacja | 7–10 minut, z krótkim pokazem aplikacji |

## 9. Ryzyka i sposoby ich ograniczenia

| Ryzyko | Skutek | Ograniczenie |
| --- | --- | --- |
| Wyniki zawyżone przez przeciek danych | Fałszywie wysoka skuteczność | Usunięcie IP, portów i czasu; podział grupowy; porównanie z podziałem losowym (E1 vs E2) |
| Szum w etykietach (np. Browsing obejmuje przepływy przeglądarki złapane przy innych czynnościach) | Pomyłki między WWW a pozostałymi klasami | Analiza macierzy pomyłek; opis ograniczenia w raporcie |
| Nierówne liczności klas | Model faworyzuje dużą klasę | Wagi klas, F1 makro jako główna miara |
| Brak definicji sesji w gotowym CSV | Trudność w podziale grupowym | Sesje odtworzone z adresów i czasu przed ich usunięciem; definicja opisana w raporcie |
| Serwer z danymi CIC niedostępny | Opóźnienie startu | Wcześniejsze pobranie; ewentualnie kopia z innego repozytorium po sprawdzeniu zgodności |
| Różnice wersji CICFlowMeter przy własnych przechwyceniach | Cechy niezgodne z danymi treningowymi | Ta sama lista kolumn; kontrola rozkładów cech przed testem E7 |
| Brak dostępu do VPN przy własnych przechwyceniach | E7 tylko dla ruchu zwykłego | Akceptowalne; opisane jako ograniczenie |
| Brak czasu pod koniec semestru | Niedokończone etapy | E6 i E7 są opcjonalne i odcinane jako pierwsze; bufor w przerwie świątecznej |

## 10. Perspektywa: praca inżynierska

Projekt zostawia gotowy potok danych i wnioski o wiarygodnej ocenie, na których można zbudować pracę inżynierską. Możliwe kierunki rozwoju:

- **Prawdziwy ruch zamiast laboratoryjnego:** zbiór [CESNET-QUIC22](https://zenodo.org/record/7409923) (ruch QUIC z sieci szkieletowej CESNET2), wczytywany biblioteką [cesnet-datazoo](https://github.com/CESNET/CESNET-Datazoo).
- **Wczesna klasyfikacja na dużą skalę:** CESNET-QUIC22 zawiera sekwencje rozmiarów, kierunków i odstępów 30 pierwszych pakietów każdego przepływu.
- **Klasyfikacja na żywo:** aplikacja przechwytująca ruch z karty sieciowej i klasyfikująca przepływy w czasie zbliżonym do rzeczywistego.
- **Klasyfikacja hierarchiczna:** najpierw typ ruchu (zwykły, VPN, Tor), potem usługa; więcej kategorii usług.
- **Modele sekwencyjne** (np. sieci neuronowe na sekwencjach pakietów) porównane z modelami z tego projektu.

## 11. Literatura wstępna i źródła danych

**Zbiory danych**

- [ISCX VPN-nonVPN 2016 – opis zbioru (UNB CIC)](https://www.unb.ca/cic/datasets/vpn.html)
- [CIC-Darknet2020 – opis zbioru (UNB CIC)](https://www.unb.ca/cic/datasets/darknet2020.html)
- [CESNET-QUIC22 (Zenodo)](https://zenodo.org/record/7409923) oraz biblioteka [CESNET DataZoo](https://github.com/CESNET/CESNET-Datazoo)

**Publikacje**

1. G. Draper-Gil, A. H. Lashkari, M. Mamun, A. A. Ghorbani, [Characterization of Encrypted and VPN Traffic Using Time-Related Features](https://www.scitepress.org/Papers/2016/57407/pdf/index.html), ICISSP 2016.
2. A. H. Lashkari, G. Kaur, A. Rahali, [DIDarknet: A Contemporary Approach to Detect and Characterize the Darknet Traffic using Deep Image Learning](https://dl.acm.org/doi/10.1145/3442520.3442521), ICCNS 2020.
3. [Darknet Traffic Classification and Adversarial Attacks](https://arxiv.org/pdf/2206.06371), arXiv 2022 (opis zbioru CIC-Darknet2020).
4. N. Wickramasinghe, A. Shaghaghi, G. Tsudik, S. Jha, [SoK: Decoding the Enigma of Encrypted Network Traffic Classifiers](https://arxiv.org/abs/2503.20093v4), arXiv 2025.
5. Y. Zhao i in., [The Sweet Danger of Sugar: Debunking Representation Learning for Encrypted Traffic Classification](https://arxiv.org/pdf/2507.16438), 2025.
6. [Mitigating the Generalization Gap in Flow-Based VPN Traffic Classification](https://eajournals.org/ejcsit/wp-content/uploads/sites/21/2026/08/Category.pdf), European Journal of Computer Science and Information Technology, 2026.
7. S. Rezaei, X. Liu, [How to Achieve High Classification Accuracy with Just a Few Labels: A Semi-supervised Approach Using Sampled Packets](https://arxiv.org/pdf/1812.09761), arXiv 2018 (zbiór UC Davis QUIC).
8. J. Luxemburk i in., CESNET-QUIC22: A large one-month QUIC network traffic dataset from backbone lines, Data in Brief, 2023 ([Zenodo](https://zenodo.org/record/7409923)).

Listę uzupełnię w etapie przeglądu literatury (do 2.11.2026).
