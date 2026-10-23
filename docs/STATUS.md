# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-23 · Branch: main · Last gate: standard @ 79baed5 - PASS with notes (etap 05, fe83fca..79baed5); 7 uwag poprawionych w b31a711, quick po poprawkach: PASS (pytest 128 passed)

## Stage
Etap 05 (E5 i modele finalne, zamyka M4 21.12): na PC gotowy, zostało sprawdzenie na laptopie. M1 oddany, M2 i M3 domknięte.
Etap 05 od: fe83fca

## Done (with evidence)
- Etapy 00–04: źródła, literatura, dane, moduł treningu, E1–E4, P1–P3 - 7029514, ed67593, a152c2a, 66bb9b0, 4e2f68d, 436ceac, 8e81ad5, 102e2c4
- Etap 05, kod: `src/finalize.py` (sesje odłożone, potoki, metadata.json), `src/model_store.py` (wczytywanie: wersje, SHA-256, ostrzeżenia = błąd), `src/check_models.py`, `src/e5_audio.py`, `tests/test_finalize.py` - e45bdf6, poprawki po /gate b31a711
- Decyzje autora (decyzje.md, wpis etapu 05): zadania aplikacji www_video_tor + voip_video_vpncamp (główne) i uslugi3_plain (odniesienie); cechy `bez_skrotow`; wspólny zbiór 12 sesji odłożonych (83 przepływy); metadata.json w gicie i w Release; rewizja P2 zaakceptowana
- 9 potoków (k-NN, drzewo, RF × 3 zadania), metadata.json - 856aa2e (`dirty=false`; .joblib bit w bit jak z e45bdf6); F1 wewn. CV RF 0,801 / 0,950 / 0,723
- Release models-v1 opublikowany (9 × .joblib + metadata.json, ok. 22 MB); metadata.json w Release = w gicie (SHA-256 4b2bceb1…)
- E5: Audio prawie wyłącznie jako Video (VoIP ≤ 1,5%); efekt kampanii: WWW w Tor-nonTor 29,1% vs 2,4% (RF) - `reports/results/05_e5/`, f8e9c12 (`dirty=false`)
- Na PC `src/check_models.py`: 9 potoków wczytanych i przewidzianych bez ostrzeżeń - b31a711
- `.venv/Scripts/python -m pytest -q` → 128 passed (b31a711)

## In progress (uncommitted)
- brak (poza tym STATUS.md i briefem)

## Next step
Etap 05, sprawdzenie na laptopie (docs/prompty/05_e5_modele_finalne.md, GOTOWE GDY) · Scope: tylko odczyt; czysty klon, `.venv` z requirements.txt, `gh release download data-processed-v1` i `models-v1` według docs/srodowisko.md, `python src/check_models.py` · Done when: skrypt wypisuje `OK: 9 potoków…` bez błędów i ostrzeżeń o wersjach; potem zamknięcie etapu (krótki wpis w decyzje.md, commit, `/handoff następny etap: docs/prompty/06_e7_wlasne_przechwycenia.md`)

## Open decisions
- brak

## Blockers
- brak

## To verify
- Laptop: Python 3.13 i identyczne wersje z requirements.txt (check_models porównuje Pythona do 3.13, biblioteki dokładnie)
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach
- Etap 09: dopasowanie kluczy sesji w surowym Darknet.CSV według `metadata.json` → `holdout.match_rules` (n_flows liczone po filtrze tła i czyszczeniu)

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
