# Etap 02: weryfikacja danych i testy przygotowania

```text
KONTEKST: Etap 02. Dane przygotowano 13.10 (commit e12d93f), bez testów. Przed treningiem sprawdzamy, czy dają się odtworzyć od zera, i zabezpieczamy logikę testami.
CZYTAJ: docs/STATUS.md, reports/preprocess_report.md, docs/decyzje.md (wpisy „Ruch tła w etykietach usług” i „Definicja sesji”)
CEL: flows.parquet odtwarzalny z surowego pliku, a filtr ruchu tła i podział na sesje pokryte testami.
ZAKRES: odtworzenie danych z Release data-raw-v1 w katalogu tymczasowym i porównanie z Release data-processed-v1; testy pytest dla src/preprocess.py (filtr ruchu tła, adresy multicast/broadcast, przypisanie sesji); poprawki błędów, które testy wykażą.
USTALENIA: testy na małych, ręcznie zbudowanych ramkach danych, bez pełnego CSV. Definicja sesji daje kilka przypadków brzegowych: przerwa dokładnie 5 min, para IP w odwrotnej kolejności, ta sama para z inną etykietą.
NIE RUSZAJ: definicji sesji ani listy filtrowanych portów. Ich zmiana to nowa decyzja autora w decyzje.md; jeśli test pokaże problem z samą definicją, opisz go i zapytaj.
ZAPISZ: wynik porównania w decyzje.md.
GOTOWE GDY: odtworzone dane zgadzają się z data-processed-v1 albo każda różnica wynika z opisanej poprawki; w tym drugim przypadku powstaje Release data-processed-v2, a nowe liczności trafiają do reports/preprocess_report.md, CLAUDE.md (sekcja o flows.parquet) i docs/srodowisko.md. pytest przechodzi.
STOP: pokaż wynik porównania i testów, uruchom /gate od SHA startu etapu; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
