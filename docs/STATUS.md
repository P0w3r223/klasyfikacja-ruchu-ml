# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-22 · Branch: main · Last gate: standard @ 6634fda - PASS with notes (pkt 1–8 poprawione w 4e2f68d)

## Stage
M3 domknięty (etap 03b, E1/E2, odpowiedź na P2), w toku etap 04: E3/E4 (część M4, termin 21.12). M1 oddany, M2 domknięty.
Etap 04 od: 669190d

## Done (with evidence)
- Inicjalizacja repo, dane, EDA, efekt kampanii - 44e96a6, e12d93f, 453e516, 99ffabc
- Etapy 00–02: źródła (E6 no-go z warunkiem powrotu), literatura, dane odtwarzalne bajt w bajt - 7029514, ed67593, a152c2a, 834ba70
- Etap 03a: schemat oceny (zagnieżdżona CV 5×3 po sesjach), src/evaluate.py zamrożony, rejestr src/experiments.py, CLI src/train.py - 35c75d0, 66bb9b0
- Etap 03b: E1/E2 dla 3 zadań × 4 modeli + wrażliwość (próg 15 min, opcja D: grupowanie po parze IP, tylko RF/Dummy) - 435c6ac, e2a31ab; wyniki z czystego drzewa (run.json: commit 8a5d4b1, dirty=false), dwa przebiegi identyczne poza czasami - 8a5d4b1
- Etap 03b: tabela reports/results/03b_tabela.md, rysunki 08–11, skrypt src/make_figures_03b.py - 6634fda, 4e2f68d
- Etap 03b: odpowiedź na P2 w docs/decyzje.md (k-NN zawyżony 0,025–0,033, drzewo 0,006–0,015, RF nieodróżnialny od szumu; zadanie 3 usług zawyżone efektem kampanii: czułość Video VPN-nonVPN 99,7% vs Tor-nonTor 84,2%) - 6634fda, 4e2f68d
- Decyzja autora: zadanie 3 usług na 3 foldach zewnętrznych (największa sesja VoIP = 30% przepływów VoIP) - docs/decyzje.md, e2a31ab
- `.venv/Scripts/python -m pytest -q` → 79 passed (4e2f68d)

## In progress (uncommitted)
- brak

## Next step
Etap 04: E3 i E4 (docs/prompty/04_e3_e4.md), zwykle 2 sesje: najpierw E3 · Scope: wpisy w src/experiments.py, hak na ważność permutacyjną w src/train.py, reports/results/, reports/figures/, P3 i P1 w docs/decyzje.md · Done when: tabela E3 (4 warianty × 4 modele z rozrzutem), tabela E4 (warianty cech × modele × zadania), ranking grup cech, odpowiedzi na P3 i P1

## Open decisions
- Wniosek z P2 „E3–E5 raportujemy z podziałem po sesjach, RF najbardziej odporny” - zapisany jako do potwierdzenia przez autora (docs/decyzje.md)
- models/metadata.json w gicie (wyjątek w .gitignore) czy tylko w Release models-v1 - decyzja w etapie 05

## Blockers
- brak

## To verify
- E3 VPN→VPN i plain→VPN: VoIP VPN ma 25 sesji; StratifiedGroupKFold wyrównuje przepływy, nie sesje, więc fold z dużą sesją może dostać 1 sesję VoIP (jak w 3 usługach w 03b). Sprawdź rozkład sesji per fold przed przebiegiem.
- Ważność permutacyjna w E4: run_experiment odrzuca dopasowany potok po metrykach; potrzebny hak w train.py (callback per fold), evaluate.py bez zmian (/gate 03a, pkt 2)
- Przy n_repeats>1 summary.csv liczy odchylenie po wszystkich foldach wszystkich powtórzeń (/gate 03a, pkt 5)
- Etap 05: fit_final ma używać evaluate.fit_tuned na całej populacji bez sesji pokazowych
- Wysokie F1 w VoIP vs Video może wynikać z Protocol (VoIP głównie UDP) i cech TCP - sprawdza E4
- Sekcja „efekt kampanii” w 03b_tabela.md wymaga lokalnych predictions.parquet (poza gitem); na laptopie się nie odtworzy
- SHA-256 Darknet.CSV vs plik z formularza UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Liczby [N] w docs/research/literatura.md przed użyciem w raporcie
- Znane: reguła `.255` usuwa 3 przepływy Video TCP błędnie; konflikty etykiet: 1 grupa VoIP NonVPN↔VPN o identycznych cechach (E3)

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
