# Etap 07: E6, wczesna klasyfikacja (VoIP vs Video na PCAP-ach ISCX VPN-nonVPN)

Dla autora: na start sesji 1 wklej listę plików z katalogu `PCAPs` (nazwy i rozmiary) ze strony, którą pokazał formularz CIC (https://cicresearch.ca/CICDataset/ISCX-VPN-NonVPN-2016/). Archiwa pobierasz ty, na PC, gdy sesja wskaże które. Jeśli przy okazji pobierzesz `Darknet.CSV` z formularza CICDarknet2020 (http://cicresearch.ca/CICDataset/CICDarknet2020/), podaj ścieżkę do pliku.

```text
KONTEKST: Etap 07, opcjonalny, wrócił 19.11.2026: formularz CIC działa (docs/decyzje.md, wpis 2026-11-19). Złożoność MEDIUM, bez @architect. Maszyna: PC (PCAP-y ~28 GB). 2 sesje, termin 6.01.2027.
CZYTAJ: docs/STATUS.md, docs/decyzje.md (wpisy 2026-11-19 i E7 krok 1: definicje CICFlowMeter), docs/research/zrodla.md (sekcja „E6: go/no-go”), docs/plan_projektu.md §2 (P4)
CEL: odpowiedź na P4: ile pierwszych pakietów przepływu wystarcza do odróżnienia VoIP od Video.
ZAKRES:
- sesja 1: wybór archiwów (tylko VoIP i wideo, NonVPN; VPN tylko jeśli pliki zawierają ruch wewnątrz tunelu, jak przepływy VPN w Darknet); czytnik PCAP; przepływy z pakietów i cechy przez src/cic_features.py; przeniesienie etykiet z Darknet.CSV przez dopasowanie 5-krotki i czasu, z raportem liczby dopasowanych i niedopasowanych przepływów; kontrola zgodności cech „pełnego przepływu” z wierszami Darknet.CSV;
- sesja 2: cechy z pierwszych N pakietów (N = 5, 10, 20, 50) i z pełnego przepływu, zestaw bez_skrotow, k-NN, drzewo i RF modułem z etapu 03a, podział po sesjach (definicja sesji jak w preprocess.py), wykres i odpowiedź na P4.
USTALENIA:
- Etykieta pochodzi z dopasowania do Darknet.CSV, nie z nazwy pliku (rozmowy `*_video*` mogą być VoIP). Przepływy bez dopasowania odrzucamy i podajemy ich liczbę.
- Filtr tła i czyszczenie jak w preprocess.py, ustalone przed oceną modeli.
- Punkt odniesienia „pełny przepływ” liczy ten sam skrypt na tych samych przepływach, a nie bierzemy go z E2.
- Czytnik pakietów to nowa zależność: przed instalacją zapytaj autora (np. dpkt vs NFStream); trafia do requirements.txt z przypiętą wersją. Laptop jej nie potrzebuje do aplikacji.
- PCAP-y i pochodne zostają poza gitem (data/external/); jeśli pochodne są potrzebne na drugiej maszynie, idą do nowego Release.
- Przed eksperymentem sprawdź udział największej sesji VoIP (StratifiedGroupKFold, CLAUDE.md); przy zbyt dużej mniej foldów, decyzja autora.
- Jeśli nakład wyraźnie przekracza 2 sesje (np. dopasowanie etykiet nie działa), zatrzymaj się i zapytaj autora, czy kończymy jako „no-go”.
- Jeśli autor poda Darknet.CSV z UNB: SHA-256 vs kopia z Kaggle (data-raw-v1), wynik w decyzje.md.
NIE RUSZAJ: models/ i Release models-v1 (E6 nie zmienia modeli aplikacji), wyniki E1–E5 i E7.
ZAPISZ: src/ (czytnik PCAP, przepływy, E6) z testami, reports/results/07_e6/, rysunek w reports/figures/, odpowiedź na P4 w decyzje.md.
GOTOWE GDY: wykres F1 makro (i dokładności zbalansowanej) w funkcji N z punktem odniesienia dla pełnego przepływu, liczności dopasowania etykiet i odpowiedź na P4.
STOP: pokaż wykres i odpowiedź na P4, uruchom /gate standard od SHA startu etapu; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
