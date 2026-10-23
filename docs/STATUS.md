# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-23 · Branch: main · Last gate: standard @ 6634fda - PASS with notes (etap 03b; etap 04 jeszcze bez /gate)

## Stage
Etap 04 (E3/E4, część M4, termin 21.12) w toku: sesja 1 (E3 + P3) zrobiona, sesja 2 to E4 + P1. M1 oddany, M2 i M3 domknięte.
Etap 04 od: 669190d

## Done (with evidence)
- Etapy 00–03b: źródła, literatura, dane, moduł treningu, E1/E2 + P2 - 7029514, ed67593, a152c2a, 66bb9b0, 4e2f68d
- E3 w rejestrze: zadania voip_video_plain / _vpn / _plain2vpn (+ mieszany voip_video_vpncamp), 3 foldy (decyzja autora) - be2f498
- Zestawy cech `bez_idle` i `bez_skrotow` (`TCP_SHORTCUTS` w src/experiments.py), skrypt src/make_figures_04.py - 438498f
- Wykryty przeciek: `Idle *` = bezwzględny czas przepływu (51% przepływów), wpis w docs/decyzje.md - 83ecc31
- Wyniki E3 (3 zestawy × 4 warianty × 4 modele), tabela reports/results/04_e3_tabela.md, rysunek 12, odpowiedź na P3 w decyzje.md; przebieg z 83ecc31, dirty=false, dwa przebiegi identyczne poza czasami - 436ceac
- `.venv/Scripts/python -m pytest -q` → 81 passed (438498f)

## In progress (uncommitted)
- brak (poza tym STATUS.md i briefem)

## Next step
Etap 04, sesja 2: E4 i P1 (docs/prompty/04_e3_e4.md) · Scope: src/features.py (grupy cech, Idle * poza „czasowe”), src/experiments.py (zestawy: tylko czasowe, tylko rozmiarowe, bez Protocol; E4 dla 3 zadań z 03b na all/bez_idle/bez_skrotow), hak na ważność permutacyjną w src/train.py, src/make_figures_04.py, P1 w docs/decyzje.md · Done when: tabela E4 (warianty cech × modele × zadania), ranking grup cech (Gini + permutacyjna) per zadanie, P1 z liczbami, w tym czy usunięcie skrótów zmienia ranking modeli; potem /gate standard 669190d..HEAD i zamknięcie etapu

## Open decisions
- Gdzie przypisać `Idle *` w feature_group: osobna grupa „przeciek_czasu” (rekomendacja) czy usunięcie z puli cech E4
- Czy E1/E2 przeliczyć bez `Idle *` jako uzupełnienie tabeli 03b (wyniki 03b zostają nietknięte) - rekomendacja: tak, jako część E4
- Wniosek z P2 „E3–E5 z podziałem po sesjach, RF najbardziej odporny” - do potwierdzenia przez autora; po E3 RF jest najbardziej wrażliwy na przeciek Idle (zwykły → VPN 0,486)
- models/metadata.json w gicie czy tylko w Release models-v1 - decyzja w etapie 05

## Blockers
- brak

## To verify
- E1/E2 (03b) mogą być zawyżone przez Idle * także przy podziale po sesjach (duża sesja VoIP: 100% z Idle vs 3% bez) - sprawdzi E4
- Ważność permutacyjna: run_experiment odrzuca dopasowany potok; potrzebny callback per fold w train.py, evaluate.py bez zmian (/gate 03a, pkt 2)
- feature_group to heurystyka po nazwach - sprawdzić przypisanie przed P1 (prompt etapu)
- Wariant „tylko czasowe” vs Draper-Gil [1]: różnice narzędzia, liczby cech, podziału z docs/research/literatura.md
- Uruchamiając eksperymenty, nie edytuj plików śledzonych (flaga dirty w run.json); reports/figures/ nie jest wyłączony z dirty
- Etap 05: fit_final przez evaluate.fit_tuned; zbiór cech modelu finalnego po wynikach E4 (bez Idle *)
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
