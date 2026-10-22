# Etap 00: weryfikacja źródeł, zamienniki i ocena wykonalności E6

Dla autora: jeśli masz już `Darknet.CSV` pobrany przez formularz UNB, podaj ścieżkę na starcie sesji.

```text
KONTEKST: Etap 00 z docs/prompty/README.md. Dane i EDA są gotowe (M2); ten etap ocenia ryzyko źródeł, nie powtarza pracy. Przy okazji zapada decyzja, czy robimy opcjonalny E6.
CZYTAJ: docs/STATUS.md, docs/plan_projektu.md §2 (P4), §4.5 i §11, docs/decyzje.md (wpisy z 2026-10-13 „Źródło danych” i „Wstępny przegląd”)
CEL: krótka ocena, czy źródła projektu są najlepszym dostępnym wyborem, zamienniki na wypadek, gdy któreś okaże się niedostępne, oraz rekomendacja go/no-go dla E6.
ZAKRES: zbiór główny CIC-Darknet2020 (kopia z Kaggle vs serwer UNB); narzędzie do liczenia cech przepływów do E7 (CICFlowMeter i alternatywy); CESNET-QUIC22 jako perspektywa; E6: dostępność i rozmiar PCAP-ów z wideo, VoIP i WWW, zgodność ich etykiet z CIC-Darknet2020 i nakład na własny skrypt cech z pierwszych N pakietów (N = 5, 10, 20, 50). Jeśli autor ma plik z formularza UNB, porównaj jego SHA-256 z sumą w decyzje.md.
USTALENIA: „lepsze źródło” oznacza tu: WWW, VoIP i wideo zebrane w jednej kampanii pomiarowej (najlepiej także przez VPN), cechy zgodne z CICFlowMeter albo surowe PCAP-y, licencja pozwalająca na użycie w raporcie, rozmiar do obróbki na PC. Największa słabość obecnych danych to efekt kampanii, więc zamiennik, który go usuwa, ma największą wartość. E6 jest „go”, gdy PCAP-y da się pobrać bez nowych barier, mieszczą się na PC, a skrypt cech da się napisać i przetestować w 1–2 sesjach; WWW w CIC-Darknet2020 pochodzi z kampanii Tor-nonTor, więc PCAP-y WWW mogą wymagać drugiego zbioru. Badanie krótkie: jeden przebieg.
NIE RUSZAJ: data/ i src/. Podmiana danych unieważnia część M2, więc decyzję podejmuje autor po przeczytaniu propozycji.
ZAPISZ: docs/research/zrodla.md: dla każdego źródła stan i dostępność, ryzyko, zamiennik, koszt podmiany (co trzeba powtórzyć) i rekomendacja: zostaje / zapas / do rozważenia; osobna sekcja „E6: go/no-go” z uzasadnieniem.
GOTOWE GDY: każde źródło z ZAKRESU ma ocenę i co najmniej jeden zamiennik albo uzasadnienie, że zamiennika nie ma; dostępność, licencja i rozmiar sprawdzone bezpośrednio na stronie źródła; E6 ma rekomendację go/no-go.
STOP: pokaż tabelę propozycji i rekomendację dla E6, zapytaj autora o decyzje; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
