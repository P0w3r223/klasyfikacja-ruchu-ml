# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-20 · Branch: main · Last gate: standard @ 68c4520 - PASS with notes (etap 08); poprawki po gate w 4ec0d59 - quick, PASS (pytest 214 passed)

## Stage
Etap 08 (zestawienie wyników) zamknięty; następny etap 09 (Streamlit, M5 17.01.2027). M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne, E5 i zestawienie wyników; eksperymenty E1–E7 policzone.

## Done (with evidence)
- Etapy 00–07 (E1–E7, modele w Release models-v1, E6 / P4) - do e5cf6e6, /gate 01a52be
- Test kampanii jako skrypt `src/campaign_test.py` → `reports/results/04_kampania/` (0,997 / bez skrótów 0,982, zgodne z 23.10; run.json dirty=false) - 217d2d0, cba7ac2
- Zestawienie wyników: `src/make_figures_08.py` (orkiestrator), `src/wyniki_dane.py` (wspólne dane rysunków i tabel), `src/figures_08.py`, `src/wyniki_tabele.py` → `reports/wyniki.md` (szkic: P1–P4, oś opowieści, ograniczenia), `reports/wyniki_tabele.md` (T1–T7), rysunki 16–17, slajdy `reports/figures/slajdy/S1–S5`; rysunki 08–15 odtwarzane bajt w bajt - 68c4520, 4ec0d59
- Szkic raportu i slajdów zaakceptowany przez autora jako baza; wersję finalną autor doprecyzuje sam (20.11)
- `.venv/Scripts/python -m pytest -q` → 214 passed (4ec0d59); test liczb: każda liczba dziesiętna z wyniki.md jest w wyniki_tabele.md

## In progress (uncommitted)
- brak (STATUS.md i brief z tego handoffu do commitu)

## Next step
Etap 09 (docs/prompty/09_streamlit.md): `app/streamlit_app.py` według planu §6.1 i pliki do pokazu w `app/demo/` (z surowego Darknet.CSV po kluczach sesji z etapu 05 oraz 1–2 pliki E7 z `reports/results/06_e7/demo/`) · Scope: `app/`, `app/demo/`, README.md (instrukcja uruchomienia) · Done when: w czystym klonie na laptopie po pobraniu models-v1 `streamlit run` działa, a każdy plik demo daje wynik w kilka sekund; potem /gate od SHA startu etapu.

## Open decisions
- Etap 09: pliki demo z Darknet.CSV wycina komputer stacjonarny (surowe dane), aplikację sprawdza laptop - kolejność maszyn ustalić na starcie etapu

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
