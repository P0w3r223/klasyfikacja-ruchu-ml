# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-22 · Branch: main · Last gate: brak (etapy 00–01 tylko dokumenty)

## Stage
M2 (dane, EDA, definicja sesji) praktycznie gotowy, M1 oddany. Etapy 00 i 01 zamknięte, następny: etap 02 (weryfikacja danych i testy przygotowania).
Etap 02 od: 878ff21

## Done (with evidence)
- Inicjalizacja repo i Releases - 44e96a6
- Źródło danych i przegląd surowego pliku - d0103c1
- Przygotowanie danych: filtr ruchu tła, czyszczenie, sesje - e12d93f
- EDA, grupy cech, potwierdzony efekt kampanii - 453e516, 99ffabc
- Kontekst w repo: CLAUDE.md, plan, wstęp M1 - 9c6278c
- M1 oddany, decyzje prowadzącego - deklaracja autora 2026-10-21 (docs/decyzje.md)
- Prompty etapów 00–13 w docs/prompty/ - 5543435
- Etap 00: ocena źródeł w docs/research/zrodla.md (E6 no-go z warunkiem powrotu; pythonowy cicflowmeter do E7) - 7029514
- Etap 01: literatura w docs/research/literatura.md: 16 prac, P1–P3 po ≥ 2 prace z liczbami sprawdzonymi u źródła; poz. 6 z §11 (EJCSIT) usunięta z raportu; wpis w docs/decyzje.md - ed67593

## In progress (uncommitted)
- brak

## Next step
Etap 02: weryfikacja danych (docs/prompty/02_weryfikacja_danych.md) · Scope: src/preprocess.py, tests/, Release data-processed-v1 · Done when: flows.parquet odtworzony od zera zgadza się z data-processed-v1 (albo różnice opisane i Release v2), pytest zielony

## Open decisions
- brak

## Blockers
- `.venv` na stacjonarnym nie działa: `.venv/Scripts/python` wskazuje na `C:\Users\Ja\AppData\Local\Programs\Python\Python313\python.exe`, którego nie ma (zauważone 22.10). Przed etapem 02 odtworzyć venv z requirements.txt. Przyczyna niesprawdzona (kopia z innej maszyny?).

## To verify
- SHA-256 Darknet.CSV vs plik z formularza UNB (autor; formularz CIC 22.10.2026 zwracał „Server error”)
- Odtwarzalność flows.parquet od zera (etap 02)
- Duplikaty przepływów w flows.parquet (etap 02; wniosek z literatury, Jerabek i in. 2025)
- Warunek powrotu E6: formularz CIC działa przed 15.12.2026 i etapy do 05 w terminie (docs/decyzje.md)
- Liczby [N] w docs/research/literatura.md (m.in. DIDarknet, Marim i in. 2023) przed użyciem w raporcie

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
