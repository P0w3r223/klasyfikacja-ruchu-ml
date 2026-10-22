# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-22 · Branch: main · Last gate: brak

## Stage
M2 (dane, EDA, definicja sesji) praktycznie gotowy, M1 oddany. Etap 00 zamknięty, następny: etap 01 (literatura, termin 2.11).

## Done (with evidence)
- Inicjalizacja repo i Releases - 44e96a6
- Źródło danych i przegląd surowego pliku - d0103c1
- Przygotowanie danych: filtr ruchu tła, czyszczenie, sesje - e12d93f
- EDA, grupy cech, potwierdzony efekt kampanii - 453e516, 99ffabc
- Kontekst w repo: CLAUDE.md, plan, wstęp M1 - 9c6278c
- M1 oddany, decyzje prowadzącego - deklaracja autora 2026-10-21 (docs/decyzje.md)
- Prompty etapów 00–13 w docs/prompty/ - 5543435
- Etap 00: ocena źródeł w docs/research/zrodla.md, decyzje autora w docs/decyzje.md (E6 no-go z warunkiem powrotu; pythonowy cicflowmeter do E7) - 7029514

## In progress (uncommitted)
- brak

## Next step
Etap 01: przegląd literatury · Scope: docs/research/literatura.md · Done when: P1–P3 mają po ≥ 2 prace z liczbami sprawdzonymi w tekście źródła

## Open decisions
- brak

## Blockers
- brak

## To verify
- SHA-256 Darknet.CSV vs plik z formularza UNB (autor; formularz CIC 22.10.2026 zwracał „Server error”)
- Odtwarzalność flows.parquet od zera (etap 02)
- Warunek powrotu E6: formularz CIC działa przed 15.12.2026 i etapy do 05 w terminie (docs/decyzje.md)

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md
