# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-19 · Branch: main · Last gate: standard @ 881df04 - PASS with notes (etap 06); etap 07 jeszcze bez /gate

## Stage
Etap 07 od: 05d901c
Etap 07 (E6: VoIP vs Video z pierwszych N pakietów na PCAP-ach ISCX VPN-nonVPN, PC, termin 6.01.2027): sesja 1 skończona, sesja 2 nierozpoczęta. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne i E5.

## Done (with evidence)
- Etapy 00–06 (E1–E5, E7, modele w Release models-v1) - do 05d901c, /gate 9b98795
- PCAP-y ISCX w `data/external/iscx_vpn2016/` (5 archiwów, zip-y w `zip/` zostają, decyzja autora); czytnik dpkt 1.9.8 (decyzja autora) w requirements.txt - 0a419a4
- `src/pcap_flows.py` (PCAP/PCAPNG po zawartości, Ethernet i raw IP) i `src/e6.py przeplywy|dopasuj` z testami - 0a419a4
- Poprawka `cic_features`: `Fwd Act Data Pkts` bez 1. pakietu (Darknet: zawsze ≤ Total Fwd − 1) - c082c51; `pytest -q` → 194 passed
- Dopasowanie etykiet (5-krotka + czas, UTC−3 h, tolerancja 1 s): pokrycie wierszy Darknet VoIP/Video 95–99%, po czyszczeniu NonVPN Video 2612 / VoIP 202, VPN Video 982 / VoIP 187; 95,5% przepływów ma wszystkie 55 cech równe Darknet.CSV - a07bb10, `reports/results/07_e6/dopasowanie.md`, wpis w decyzje.md

## In progress (uncommitted)
- brak (STATUS.md i brief z tego handoffu do commitu)

## Next step
Etap 07, sesja 2 (docs/prompty/07_e6_wczesna_klasyfikacja.md): cechy z pierwszych N = 5, 10, 20, 50 pakietów i z pełnego przepływu z `data/external/iscx_e6/` (przepływy trzeba zachować z pakietami albo przeliczyć z PCAP-ów, ok. 10 min), zestaw bez_skrotow, k-NN/drzewo/RF modułem z 03a, podział po sesjach, zadanie VoIP vs Video w kampanii VPN-nonVPN · Scope: `src/e6.py` (+ ewentualnie `src/pcap_flows.py`), testy, `reports/results/07_e6/`, rysunek w `reports/figures/` · Done when: wykres F1 makro i dokładności zbalansowanej w funkcji N z punktem odniesienia dla pełnego przepływu i odpowiedź na P4 w decyzje.md; potem /gate standard 05d901c..HEAD i zamknięcie etapu.

## Open decisions
- Liczba foldów: największa sesja VoIP ≈ 16% klasy w kampanii VPN-nonVPN (31% w samym NonVPN) - sprawdzić przed przebiegiem; przy problemie mniej foldów (decyzja autora)
- Czy E6 ma też wariant tylko NonVPN (VoIP 202, 2 pliki źródłowe) - domyślnie nie, cała kampania jak E2 `voip_video_vpncamp`

## Blockers
- brak

## To verify
- E7 policzony starą definicją `Fwd Act Data Pkts` (+1 przy ładunku w 1. pakiecie); wyniki E7 nieprzeliczane (decyzje.md, wpis E6 sesja 1)
- Raport: VoIP w Darknet to tylko VoIPBuster, rozmowy głosowe to Audio-Streaming, rozmowy wideo to Video - opisać przy E3 i E5
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- SHA-256 Darknet.CSV vs UNB: formularz CICDarknet2020 powinien działać; autor podaje ścieżkę pliku
- Etap 09: dopasowanie kluczy sesji według `metadata.json` → `holdout.match_rules`; pliki demo E7 mają zastępcze IP i powtarzalne `Flow ID` (bez deduplikacji po `Flow ID`)
- Raport: VoIP USBVPN2022 to 62 przepływy z jednego spotkania; wynik tej klasy z licznością i bez wniosków ogólnych

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
