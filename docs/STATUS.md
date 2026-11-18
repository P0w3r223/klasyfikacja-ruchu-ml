# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-18 · Branch: main · Last gate: standard @ 79baed5 - PASS with notes (etap 05, fe83fca..79baed5); 7 uwag poprawionych w b31a711, quick po poprawkach: PASS (pytest 128 passed)

## Stage
Etap 06 od: 6677412

Etap 06 (E7 na USBVPN2022), sesja 1 zakończona: cechy policzone, rozkłady porównane i pokazane autorowi, **przed oceną modeli**. CZYTAJ w sesji 2: docs/prompty/06_e7_zbior_zewnetrzny.md (USTALENIA, ZAPISZ, GOTOWE GDY) oraz wpis „E7, krok 1” w docs/decyzje.md. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma gotowe modele finalne i E5.

## Done (with evidence)
- Etapy 00–05: źródła, literatura, dane, moduł treningu, E1–E5, modele finalne w Release models-v1 - 7029514 … f8e9c12, laptop 8ddccc0
- Etap 06, sesja 1: `src/cic_features.py` (55 cech, definicje sprawdzone na Darknet), `src/usbvpn.py` (pobranie z MD5, JSON z zip, filtr, scalanie rekordów pmacct, rozbijanie scalonych segmentów), `src/e7.py rozklady`; testy: `pytest -q` → 160 passed - 6ed5848, ab959e3
- `data/external/usbvpn_flows.parquet` (poza gitem): WWW 42 797, Video 2 914, VoIP 62; wariant bez rozbijania: `usbvpn_flows_bez_rozbijania.parquet`
- Rozkłady: `reports/results/06_e7/rozklady.md`, `ks_heatmap.png`, `profil_ruchu.csv` (oraz `bez_rozbijania/`), run_rozklady.json dirty=false @ ab959e3; średni KS 0,36–0,46 vs 0,17 między kampaniami Darknet

## In progress (uncommitted)
- brak

## Next step
Etap 06, sesja 2 · Scope: `gh release download usbvpn-processed-v1 -D data/external --skip-existing` (SHA-256 w opisie Release); `src/e7.py ocena`: 9 potoków przez `model_store` w www_video_tor, voip_video_vpncamp, uslugi3_plain (F1 makro, czułość per klasa, macierze pomyłek) zestawione z CV z E4; liczności części VPN; 1–2 CSV w formacie Darknet.CSV dla app/demo/ z kontrolą kolumn `input_columns`; wynik w decyzje.md · Done when: GOTOWE GDY z promptu 06, potem `/gate standard 6677412..HEAD` i zamknięcie etapu.

## Open decisions
- brak (18.11 autor wybrał oba warianty domyślne: rozbijanie scalonych segmentów, filtr bez nowej reguły; decyzje.md)

## Blockers
- brak

## To verify
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach
- Etap 09: dopasowanie kluczy sesji w surowym Darknet.CSV według `metadata.json` → `holdout.match_rules` (n_flows liczone po filtrze tła i czyszczeniu)
- Etap 06: VoIP USBVPN2022 to 62 przepływy z jednego spotkania, więc wynik tej klasy podawać z liczbą przepływów i bez wniosków ogólnych

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
