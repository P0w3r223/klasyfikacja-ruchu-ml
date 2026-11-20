# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-20 · Branch: main · Last gate: standard @ 25554f2 - PASS with notes (etap 09); poprawki po gate w 8630554 (pytest 243 passed)

## Stage
Etap 09 (Streamlit, M5 17.01.2027): kod, pliki demo i /gate gotowe na PC; brakuje kontroli na laptopie.
Etap 09 od: e8338df

Etap 08 (zestawienie wyników) zamknięty. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne, E5 i zestawienie wyników; eksperymenty E1–E7 policzone.

## Done (with evidence)
- Etapy 00–07 (E1–E7, modele w Release models-v1, E6 / P4) - do e5cf6e6, /gate 01a52be
- Test kampanii jako skrypt `src/campaign_test.py` → `reports/results/04_kampania/` (0,997 / bez skrótów 0,982, zgodne z 23.10; run.json dirty=false) - 217d2d0, cba7ac2
- Zestawienie wyników: `src/make_figures_08.py` (orkiestrator), `src/wyniki_dane.py` (wspólne dane rysunków i tabel), `src/figures_08.py`, `src/wyniki_tabele.py` → `reports/wyniki.md` (szkic: P1–P4, oś opowieści, ograniczenia), `reports/wyniki_tabele.md` (T1–T7), rysunki 16–17, slajdy `reports/figures/slajdy/S1–S5`; rysunki 08–15 odtwarzane bajt w bajt - 68c4520, 4ec0d59
- Szkic raportu i slajdów zaakceptowany przez autora jako baza; wersję finalną autor doprecyzuje sam (20.11)
- Etap 09: `app/streamlit_app.py`, `src/app_logic.py`, `src/demo_files.py` → `app/demo/` (2 pliki Darknet z sesji holdout + tło, 2 pliki E7), README z instrukcją; na PC 36 kombinacji plik × zadanie × model bez błędów, wynik < 0,2 s, ważność permutacyjna k-NN do ~7 s - 25554f2, 8630554
- `.venv/Scripts/python -m pytest -q` → 243 passed (8630554); test liczb: każda liczba dziesiętna z wyniki.md jest w wyniki_tabele.md

## In progress (uncommitted)
- brak

## Next step
Etap 09, kontrola na laptopie (docs/prompty/09_streamlit.md, GOTOWE GDY): `git pull`, `pip install -r requirements.txt`, `gh release download models-v1 -D models --skip-existing --pattern "*.joblib"`, `.venv/Scripts/python -m pytest -q`, potem `.venv/Scripts/python -m streamlit run app/streamlit_app.py` i każdy z 4 plików demo (RF i k-NN) · Done when: wynik w kilka sekund na każdym pliku, czas ważności k-NN zapisany w decyzje.md (wpis 20.11, etap 09) · Potem zamknięcie etapu: commit i push, `/handoff następny etap: docs/prompty/10_dokumentacja.md`.

## Open decisions
- brak

## Blockers
- brak

## To verify
- E7 policzony starą definicją `Fwd Act Data Pkts` (+1 przy ładunku w 1. pakiecie; usbvpn_flows.parquet, 06_e7, pliki demo); nieprzeliczany - w raporcie nie mieszać z definicją z E6
- Raport, P4: „brak wykrytej różnicy przy 3–5 foldach”, nie równoważność; liczb populacji `wszystkie` i `min20` nie zestawiać ze sobą
- Raport: VoIP w Darknet to tylko VoIPBuster (rozmowy głosowe = Audio-Streaming, wideo = Video) - opisać przy E3 i E5
- T2 w wyniki_tabele.md (czułość Video per kampania) wymaga lokalnych predictions.parquet: pełne odtworzenie `make_figures_08.py` tylko na PC
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- SHA-256 Darknet.CSV vs UNB: formularz CICDarknet2020 powinien działać; autor podaje ścieżkę pliku
- Etap 09: dopasowanie kluczy sesji według `metadata.json` → `holdout.match_rules`; pliki demo E7 mają zastępcze IP i powtarzalne `Flow ID` (bez deduplikacji po `Flow ID`)
- Raport: VoIP USBVPN2022 to 62 przepływy z jednego spotkania; wynik tej klasy z licznością i bez wniosków ogólnych

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Wyniki: reports/wyniki.md
