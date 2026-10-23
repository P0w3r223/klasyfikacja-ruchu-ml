# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-23 · Branch: main · Last gate: standard @ 79baed5 - PASS with notes (etap 05, fe83fca..79baed5); 7 uwag poprawionych w b31a711, quick po poprawkach: PASS (pytest 128 passed)

## Stage
Etap 04 (E3/E4) zamknięty: P3 i P1 odpowiedziane, P2 zrewidowane. Trwa etap 05 (E5 i modele finalne, zamyka M4 21.12). M1 oddany, M2 i M3 domknięte.
Etap 05 od: fe83fca

## Done (with evidence)
- Etapy 00–03b: źródła, literatura, dane, moduł treningu, E1/E2 - 7029514, ed67593, a152c2a, 66bb9b0, 4e2f68d
- E3 (4 warianty × 3 zestawy cech × 4 modele) i P3 - 436ceac; porównanie parami po foldach - 102e2c4
- E4: 7 zestawów cech × 4 modele × 3 zadania, ważność grup (Gini + permutacja grupy), P1, rewizja P2 - c6d9f5f (kod), 8e81ad5 (wyniki, `dirty=false`); `e4_all_*` = E2 z 03b bit w bit
- `Idle *` jako grupa `przeciek_czasu`; zestawy `tylko_czasowe`, `czasowe_tempo`, `tylko_rozmiarowe`, `bez_protocol` w src/experiments.py - c6d9f5f
- Wrażliwość E2 bez skrótów (`e2_bez_skrotow_*`): wniosek z 03b się utrzymuje - 102e2c4
- Efekt kampanii bez przecieku: 0,982 bez skrótów (wpis E4 w decyzje.md) - 102e2c4
- Poprawki po /gate: próg sesji z features.json obok `--data`, stan gita przed/po przebiegu, kontrola uszkodzonych wierszy, udział sesji per klasa, testy - 85b856c
- Etap 05: kod finalize/model_store/check_models/e5_audio + testy - e45bdf6; 9 potoków `bez_skrotow`, 12 sesji odłożonych, metadata.json - 856aa2e (po /gate; .joblib bit w bit jak w e45bdf6); Release models-v1 opublikowany, metadata.json podmieniony; E5 (`reports/results/05_e5/`, `dirty=false`), wpis w decyzje.md
- Lokalnie `src/check_models.py`: 9 potoków wczytanych i przewidzianych bez ostrzeżeń
- `.venv/Scripts/python -m pytest -q` → 128 passed (b31a711)

## In progress (uncommitted)
- brak (poza tym STATUS.md i briefem)

## Next step
Etap 05, ostatni krok: sprawdzenie na laptopie (docs/srodowisko.md: pobranie models-v1 + `src/check_models.py`) · Done when: na laptopie w czystym klonie skrypt wczytuje każdy potok z models-v1 i przewiduje na odłożonych sesjach bez błędów i ostrzeżeń o wersjach

## Open decisions
- brak (P2 zaakceptowana, cechy `bez_skrotow`, metadata.json w gicie i Release - decyzje.md, etap 05)

## Blockers
- brak

## To verify
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Zwykły → VPN trenuje ten sam model w każdym foldzie 3×: koszt, nie błąd
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
