# STATUS - klasyfikacja-ruchu-ml

Updated: 2026-10-22 · Branch: main · Last gate: standard @ a152c2a - PASS with notes (pkt 1 i 3 poprawione w 06d7aba)

## Stage
M2 domknięty (dane zweryfikowane i pokryte testami), M1 oddany. Etapy 00–02 zamknięte, następny: etap 03a (moduł treningu i schemat oceny, pierwsza część M3).
Etap 03a od: 5340b25

## Done (with evidence)
- Inicjalizacja repo i Releases - 44e96a6
- Przygotowanie danych: filtr ruchu tła, czyszczenie, sesje - e12d93f
- EDA, grupy cech, potwierdzony efekt kampanii - 453e516, 99ffabc
- M1 oddany, decyzje prowadzącego - deklaracja autora 2026-10-21 (docs/decyzje.md)
- Prompty etapów 00–13 w docs/prompty/ - 5543435
- Etap 00: ocena źródeł w docs/research/zrodla.md (E6 no-go z warunkiem powrotu) - 7029514
- Etap 01: literatura w docs/research/literatura.md (16 prac) - ed67593
- Etap 02: flows.parquet odtworzony od zera identyczny bajt w bajt z data-processed-v1 (SHA-256 9cccd872…), v2 niepotrzebny; 43 testy w tests/test_preprocess.py; preprocess.py ma --raw/--out-dir/--reports-dir - a152c2a, 06d7aba, `.venv/Scripts/python -m pytest -q` → 43 passed
- Dług z /gate etapu 02: `build()` bez I/O + `main(argv)` w preprocess.py, test integracyjny na syntetycznym CSV (tests/test_preprocess_cli.py); odtworzenie z Darknet.CSV nadal daje te same SHA-256 wszystkich 4 plików wynikowych - 834ba70, `pytest -q` → 51 passed
- `.venv` odtworzony z requirements.txt (Python 3.13.2; sklearn 1.9.1, pandas 3.0.6), pytest==9.1.1 dopisany - a152c2a

## In progress (uncommitted)
- brak

## Next step
Etap 03a: moduł treningu (docs/prompty/03a_modul_treningu.md) · Scope: src/train.py, src/evaluate.py, tests/, reports/results/ (LARGE: najpierw @architect, akceptacja autora) · Done when: pytest zielony, jedno polecenie odtwarza pilotaż VoIP vs Video (4 modele, oba podziały), autor zaakceptował schemat oceny

## Open decisions
- brak

## Blockers
- brak

## To verify
- SHA-256 Darknet.CSV vs plik z formularza UNB (formularz CIC 22.10.2026 zwracał „Server error”)
- Warunek powrotu E6: formularz CIC działa przed 15.12.2026 i etapy do 05 w terminie (docs/decyzje.md)
- Liczby [N] w docs/research/literatura.md (m.in. DIDarknet, Marim i in. 2023) przed użyciem w raporcie
- Znane: reguła `.255` usuwa 3 przepływy Video TCP błędnie; przy ewentualnym v2 stosować ją tylko do UDP (docs/decyzje.md, etap 02)
- Konflikty etykiet: 1 grupa VoIP NonVPN↔VPN o identycznych cechach — uwzględnić przy interpretacji E3
## Plan
Full plan: docs/plan_projektu.md · Etapy: docs/prompty/README.md · Decyzje: docs/decyzje.md · Literatura: docs/research/literatura.md
