# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-19 · Branch: main · Last gate: standard @ 881df04 - PASS with notes (etap 06, 6677412..881df04); bez CRITICAL/HIGH, mały MSS zmierzony (≤ 0,29% scalonych segmentów) i zostawiony jako zastrzeżenie (decyzje.md)

## Stage
Etap 07 od: 05d901c
Etap 06 zamknięty (decyzje.md, wpis 2026-11-19). Następny: etap 07, E6 (VoIP vs Video na PCAP-ach ISCX VPN-nonVPN, PC, 2 sesje, termin 6.01.2027), jeszcze nierozpoczęty; na starcie sesji dopisz tu `Etap 07 od: <sha>`. M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne i E5.

## Done (with evidence)
- Etapy 00–05: źródła, literatura, dane, moduł treningu, E1–E5, modele finalne w Release models-v1 - 7029514 … f8e9c12, laptop 8ddccc0
- Etap 06 (E7 na USBVPN2022): cechy CICFlowMeter z `x_packets` (`src/cic_features.py`), ocena 9 potoków (wszystkie na poziomie zgadywania), pliki do pokazu w `reports/results/06_e7/demo/`; `pytest -q` → 172 passed - aaaa94c, 881df04, /gate 9b98795
- Formularz CIC działa (19.11, autor: katalogi `CSVs` i `PCAPs`); decyzja autora: E6 wraca; prompt 07 przepisany, README etapów i zrodla.md zaktualizowane - 4088e68

## In progress (uncommitted)
- brak

## Next step
Etap 07, sesja 1 (docs/prompty/07_e6_wczesna_klasyfikacja.md): autor wkleja listę plików z `PCAPs`, wybór archiwów VoIP i wideo, czytnik PCAP (zależność do decyzji autora), przepływy i cechy przez `src/cic_features.py`, etykiety przez dopasowanie 5-krotki i czasu do Darknet.CSV · Scope: nowy moduł w `src/` z testami, `data/external/` (poza gitem) · Done when: liczności dopasowanych i niedopasowanych przepływów VoIP/Video oraz kontrola zgodności cech pełnego przepływu z Darknet.CSV.

## Open decisions
- Czytnik PCAP: dpkt vs NFStream (albo inny) - decyzja autora w sesji 1 przed instalacją
- Czy brać pliki VPN: tylko jeśli zawierają ruch wewnątrz tunelu jak przepływy VPN w Darknet - rozstrzyga sesja 1 na danych
- Opcjonalnie do raportu: czy usługi w samym USBVPN2022 są rozróżnialne tymi cechami (wymaga treningu na USBVPN2022, poza ustaleniami E7)

## Blockers
- brak (archiwa PCAP pobiera autor na PC przez stronę formularza)

## To verify
- SHA-256 Darknet.CSV vs UNB: formularz CICDarknet2020 powinien teraz działać; autor podaje ścieżkę pliku
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach
- E6: największa sesja VoIP to 30% przepływów w ruchu zwykłym (Darknet); sprawdzić udział przed doborem foldów
- Etap 09: dopasowanie kluczy sesji w surowym Darknet.CSV według `metadata.json` → `holdout.match_rules` (n_flows liczone po filtrze tła i czyszczeniu)
- Etap 09: pliki demo E7 mają zastępcze IP (jedna para, RFC 5737) i powtarzalne `Flow ID`; aplikacja nie może usuwać duplikatów po `Flow ID`, a cały plik to jedna sesja na etykietę
- Raport: VoIP USBVPN2022 to 62 przepływy z jednego spotkania; wynik tej klasy z licznością i bez wniosków ogólnych

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
