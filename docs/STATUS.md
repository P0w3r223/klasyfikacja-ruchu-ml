# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-20 · Branch: main · Last gate: standard @ 05a2736 - PASS with notes (etap 07); poprawki po gate 01a52be (testy, docstring, decyzje.md) - quick, PASS

## Stage
Etap 08 od: e5cf6e6
Etap 08 (zestawienie wyników, PC, termin 10.01.2027) w toku; etap 07 (E6) zamknięty. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne i E5; eksperymenty E1–E7 policzone.

## Done (with evidence)
- Etapy 00–06 (E1–E5, E7, modele w Release models-v1) - do 05d901c, /gate 9b98795
- E6 sesja 1: czytnik PCAP (dpkt 1.9.8), dopasowanie etykiet do Darknet.CSV (pokrycie 95–99%, 3 983 przepływy) - 0a419a4, c082c51, a07bb10
- E6 sesja 2: cechy z pierwszych N = 5/10/20/50 pakietów (`src/e6.py prefiksy`, 0 różnic pełnego przepływu z e6_flows, 0 inf/NaN), ocena `src/e6_ocena.py`, rysunek `src/make_figures_07.py` → `reports/figures/15_e6_pierwsze_pakiety.png` - 7bd3dfa, 05a2736
- Wynik E6 / P4: 5 pierwszych pakietów nie daje wykrytej różnicy względem pełnego przepływu (RF 0,975 vs 0,957 we wszystkich przepływach; różnice parami w rozrzucie foldów); pełny przepływ odtwarza E4 bez_skrotow na Darknet (RF 0,957 vs 0,957) - `reports/results/07_e6/ocena/`, wpis 2026-11-20 w decyzje.md, `run.json` dirty=false
- `.venv/Scripts/python -m pytest -q` → 207 passed (01a52be)

## In progress (uncommitted)
- brak (STATUS.md i brief z tego handoffu do commitu)

## Next step
Etap 08 (docs/prompty/08_wyniki.md): `reports/wyniki.md` z odpowiedziami na P1–P4 z liczbami, tabela główna (zadanie × model × podział), efekt kampanii, E3, E5, E6, E7, ograniczenia; rysunki jednym skryptem z `reports/results/` · Scope: `reports/wyniki.md`, nowy skrypt w `src/`, `reports/figures/` (reports/results/ tylko do odczytu) · Done when: ponowne uruchomienie skryptu odtwarza wszystkie rysunki i tabele, a każda liczba w wyniki.md wynika z pliku w reports/results/; potem /gate od SHA startu etapu.

## Open decisions
- Etap 08: czy rysunki 08–15 z etapów 03b–07 wchodzą do wyniki.md bez zmian, czy jeden skrypt je przerysowuje w formacie slajdu - decyzja autora na starcie etapu

## Blockers
- brak

## To verify
- E7 policzony starą definicją `Fwd Act Data Pkts` (+1 przy ładunku w 1. pakiecie; usbvpn_flows.parquet, 06_e7, pliki demo); nieprzeliczany - w raporcie nie mieszać z definicją z E6 (decyzje.md, wpis E6 sesja 1)
- Raport, P4: „brak wykrytej różnicy przy 3–5 foldach”, nie równoważność; VoIP = tylko VoIPBuster (2 pliki na tunel); liczb populacji `wszystkie` (5 foldów) i `min20` (3 foldy) nie zestawiać ze sobą
- Raport: VoIP w Darknet to tylko VoIPBuster, rozmowy głosowe to Audio-Streaming, rozmowy wideo to Video - opisać przy E3 i E5
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- SHA-256 Darknet.CSV vs UNB: formularz CICDarknet2020 powinien działać; autor podaje ścieżkę pliku
- Etap 09: dopasowanie kluczy sesji według `metadata.json` → `holdout.match_rules`; pliki demo E7 mają zastępcze IP i powtarzalne `Flow ID` (bez deduplikacji po `Flow ID`)
- Raport: VoIP USBVPN2022 to 62 przepływy z jednego spotkania; wynik tej klasy z licznością i bez wniosków ogólnych

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
