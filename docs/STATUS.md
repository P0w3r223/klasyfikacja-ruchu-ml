# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-22 · Branch: main · Last gate: standard @ 5d20f43 - PASS with notes (pkt 1, 3, 4, 6 poprawione w 66bb9b0)

## Stage
M3 w toku: etap 03a (moduł treningu i schemat oceny) zamknięty, w toku etap 03b (E1/E2, zamyka M3, termin 7.12). M1 oddany, M2 domknięty.
Etap 03b od: 414d8a0

## Done (with evidence)
- Inicjalizacja repo i Releases - 44e96a6
- Przygotowanie danych, EDA, potwierdzony efekt kampanii - e12d93f, 453e516, 99ffabc
- Prompty etapów 00–13 w docs/prompty/ - 5543435
- Etap 00: ocena źródeł (E6 no-go z warunkiem powrotu) - 7029514
- Etap 01: literatura, 16 prac - ed67593
- Etap 02: dane odtwarzalne bajt w bajt (SHA-256 flows.parquet 9cccd872…), testy przygotowania, build() bez I/O - a152c2a, 06d7aba, 834ba70
- Etap 03a: schemat oceny zaakceptowany przez autora (zagnieżdżona CV 5×3 po sesjach, E1 jako StratifiedKFold 5×3, Dummy stratified, n_repeats=1) - docs/decyzje.md, 35c75d0
- Etap 03a: moduł src/evaluate.py (bez I/O, zamrożony), src/models.py, src/experiments.py (rejestr, tu dopisują etapy 03b–05), src/train.py (CLI) - 35c75d0, 66bb9b0, `.venv/Scripts/python -m pytest -q` → 72 passed
- Etap 03a: pilotaż VoIP vs Video, `python src/train.py --experiment pilot_03a` (~1 min), F1 makro po sesjach: Dummy 0,519, k-NN 0,969, drzewo 0,979, RF 0,989; losowy 0,99+ - reports/results/pilot_03a/, aef482d

## In progress (uncommitted)
- brak

## Next step
Etap 03b: E1/E2 (docs/prompty/03b_e1_e2.md) · Scope: wpisy w src/experiments.py, reports/results/, reports/figures/, odpowiedź na P2 w docs/decyzje.md · Done when: 4 modele × 3 zadania × 2 podziały (F1 makro średnia/odchylenie/per fold, F1 per klasa, accuracy, czasy, macierze) + wynik dla progu 15 min

## Open decisions
- Opcja D (grupowanie po parze IP bez czasu) jako analiza wrażliwości w 03b - robić czy pominąć (propozycja architekta, autor jeszcze nie zdecydował)
- models/metadata.json w gicie (wyjątek w .gitignore) czy tylko w Release models-v1 - decyzja w etapie 05

## Blockers
- brak

## To verify
- Ważność permutacyjna w E4 (etap 04): run_experiment odrzuca dopasowany potok po metrykach; trzeba dodać hak w train.py (np. callback per fold), evaluate.py zostaje bez zmian (/gate 03a, pkt 2)
- Przy n_repeats>1 summary.csv liczy odchylenie po wszystkich foldach wszystkich powtórzeń (zaniża rozrzut); poprawić, gdyby włączono powtórzenia (/gate 03a, pkt 5)
- Etap 05: fit_final w train.py ma używać evaluate.fit_tuned na całej populacji bez sesji pokazowych; klucz sesji z kolumn meta przed prepare()
- Wysokie F1 w pilotażu może wynikać z Protocol (VoIP głównie UDP) i cech TCP - sprawdza E4
- SHA-256 Darknet.CSV vs plik z formularza UNB (formularz CIC 22.10.2026 zwracał „Server error”)
- Warunek powrotu E6: formularz CIC działa przed 15.12.2026 i etapy do 05 w terminie (docs/decyzje.md)
- Liczby [N] w docs/research/literatura.md (m.in. DIDarknet, Marim i in. 2023) przed użyciem w raporcie
- Znane: reguła `.255` usuwa 3 przepływy Video TCP błędnie; przy ewentualnym v2 stosować ją tylko do UDP
- Konflikty etykiet: 1 grupa VoIP NonVPN↔VPN o identycznych cechach - uwzględnić przy interpretacji E3

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
