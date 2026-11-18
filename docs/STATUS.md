# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-11-18 · Branch: main · Last gate: standard @ 881df04 - PASS with notes (etap 06, 6677412..881df04); bez CRITICAL/HIGH, mały MSS zmierzony (≤ 0,29% scalonych segmentów) i zostawiony jako zastrzeżenie (decyzje.md)

## Stage
Etap 06 od: 6677412

Etap 06 (E7 na USBVPN2022) gotowy: ocena, pliki do pokazu, /gate PASS with notes, wpis w decyzje.md, push (9b98795). **Niezamknięty formalnie:** `/handoff` z następnym etapem czeka na sprawdzenie formularza CIC przez autora (warunek powrotu E6). M1 oddany, M2 i M3 domknięte, M4 (21.12) ma modele finalne i E5.

## Done (with evidence)
- Etapy 00–05: źródła, literatura, dane, moduł treningu, E1–E5, modele finalne w Release models-v1 - 7029514 … f8e9c12, laptop 8ddccc0
- Etap 06, sesja 1: cechy CICFlowMeter z USBVPN2022 i rozkłady KS przed oceną - 6ed5848, ab959e3, Release usbvpn-processed-v1
- Etap 06, sesja 2: `src/e7.py ocena|demo`, `src/e7_ocena.py`, `src/darknet_csv.py`, `model_store.missing_input_columns`, `src/usbvpn.py vpn`; `pytest -q` → 172 passed - aaaa94c
- Wynik E7 (run_ocena.json dirty=false @ aaaa94c, `reports/results/06_e7/ocena/`): wszystkie 9 potoków na poziomie zgadywania (dokł. zbalansowana 0,49–0,55 w 2 klasach, 0,35–0,39 w 3 usługach; RF F1 makro 0,797→0,469, 0,957→0,545, 0,713→0,108); część VPN: 1 połączenie tunelu na plik (`usbvpn_vpn.md`) - 881df04
- Pliki do pokazu: `reports/results/06_e7/demo/usbvpn2022_www_video.csv`, `usbvpn2022_voip_video.csv` (kontrola kolumn, filtr tła OK) - 881df04

## In progress (uncommitted)
- brak

## Next step
Autor: wysłać formularz https://cicresearch.ca/CICDataset/ISCX-VPN-NonVPN-2016/ (18.11 strona i `insert.php` odpowiadają, komunikat „Server error” jest ukryty do czasu wysłania; samo GET nic nie rozstrzyga). · Gdy pokaże „Ready / Browse files”: warunek powrotu E6 spełniony → przepisać docs/prompty/07_e6_wczesna_klasyfikacja.md (VoIP vs Video na PCAP-ach VPN-nonVPN, ~28 GB, PC) i przy okazji SHA-256 Darknet.CSV vs UNB. Gdy błąd: E6 no-go, następny etap 09 (Streamlit, docs/prompty/09_streamlit.md). · Done when: `/handoff następny etap: docs/prompty/<plik>`, commit i push STATUS.md i `.claude/sessions/` (zamyka etap 06).

## Open decisions
- Następny etap: 07 (E6, jeśli formularz CIC działa) albo 09 (Streamlit) - zależy od testu formularza przez autora
- Opcjonalnie do raportu: czy usługi w samym USBVPN2022 są rozróżnialne tymi cechami (wymaga treningu na USBVPN2022, poza ustaleniami E7)

## Blockers
- brak

## To verify
- `reports/figures/` nie jest wyłączony z flagi dirty: skrypty rysunków uruchamiaj po przebiegach i commituj przed kolejnymi
- Notatnik EDA (02) ma dawną grupę „czasowe” z `Idle *`; nieprzeliczany, opisane w decyzje.md
- SHA-256 Darknet.CSV vs UNB; warunek powrotu E6: formularz CIC działa przed 15.12.2026
- Znane: reguła `.255` usuwa 3 przepływy Video TCP; 1 grupa VoIP NonVPN↔VPN o identycznych cechach
- Etap 09: dopasowanie kluczy sesji w surowym Darknet.CSV według `metadata.json` → `holdout.match_rules` (n_flows liczone po filtrze tła i czyszczeniu)
- Etap 09: pliki demo E7 mają zastępcze IP (jedna para, RFC 5737) i powtarzalne `Flow ID`; aplikacja nie może usuwać duplikatów po `Flow ID`, a cały plik to jedna sesja na etykietę
- Raport: VoIP USBVPN2022 to 62 przepływy z jednego spotkania; wynik tej klasy z licznością i bez wniosków ogólnych
- Lokalny `git stash` na PC („lokalny STATUS sprzed pull 18.11”) jest nieaktualny; do usunięcia (`git stash drop`)

## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
