# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-18 · Branch: main · Last gate: standard @ 79baed5 - PASS with notes (etap 05, fe83fca..79baed5); 7 uwag poprawionych w b31a711, quick po poprawkach: PASS (pytest 128 passed)

## Stage
Etap 06 od: 6677412

Etap 05 zamknięty 18.11 (sprawdzenie na laptopie, 8ddccc0). Następny: etap 06 (E7, test na zbiorze zewnętrznym USBVPN2022; 18.11 zamiast własnych nagrań, decyzje.md), jeszcze nie rozpoczęty; linię `Etap 06 od: <sha>` wpisuje pierwsza sesja etapu po `git pull`. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma gotowe modele finalne i E5.

## Done (with evidence)
- Etapy 00–04: źródła, literatura, dane, moduł treningu, E1–E4, P1–P3 - 7029514, ed67593, a152c2a, 66bb9b0, 4e2f68d, 436ceac, 8e81ad5, 102e2c4
- Etap 05: `src/finalize.py`, `src/model_store.py`, `src/check_models.py`, `src/e5_audio.py`, 9 potoków w Release models-v1, `models/metadata.json` w gicie, E5 w `reports/results/05_e5/` - e45bdf6, b31a711, 856aa2e, f8e9c12
- Laptop 18.11: Python 3.13.15, biblioteki zgodne z requirements.txt, SHA-256 danych = data-processed-v1; `src/check_models.py` → `OK: 9 potoków…` bez ostrzeżeń, wyniki na sesjach odłożonych jak na PC (RF 0,821 / 0,945 / 0,726); `pytest -q` → 128 passed; wpis w decyzje.md - 8ddccc0

## In progress (uncommitted)
- brak

## Next step
Etap 06, sesja 1 (docs/prompty/06_e7_zbior_zewnetrzny.md) · Scope: pobranie USBVPN2022 z Zenodo z kontrolą MD5, `src/usbvpn.py` liczący 55 cech `bez_skrotow` z `x_packets` z testami, reguła filtra infrastruktury i tła, porównanie rozkładów cech z Darknet · Done when: rozkłady pokazane autorowi przed oceną modeli, potem `/handoff` (sesja 2: ocena 9 potoków i pliki do pokazu). Maszyna: laptop wystarcza (archiwum 812 MB, czytane z zip).

## Open decisions
- brak

## Blockers
- brak

## To verify
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach
- Etap 09: dopasowanie kluczy sesji w surowym Darknet.CSV według `metadata.json` → `holdout.match_rules` (n_flows liczone po filtrze tła i czyszczeniu)
- Etap 06: czy `bytes` w `x_packets` to długość pakietu IP czy ładunku, i jak traktować scalone segmenty do ~16 KB; czy przepływy pmacct trzeba ciąć według reguł CICFlowMeter (timeout 120 s, FIN)

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
