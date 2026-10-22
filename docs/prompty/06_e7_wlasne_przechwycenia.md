# Etap 06: E7, własne przechwycenia ruchu

Dla autora: nagrania wykonujesz sam, według scenariusza z pierwszej sesji tego etapu. Druga sesja zaczyna się, gdy pliki są w `data/own/`.

```text
KONTEKST: Etap 06, zwykle 2 sesje rozdzielone nagraniami autora. Sprawdzamy, czy modele z danych z lat 2015–2016 rozpoznają ruch przechwycony samodzielnie w 2026 r.
CZYTAJ: docs/STATUS.md, docs/research/zrodla.md (narzędzie do cech przepływów), docs/plan_projektu.md §4.5 i §9
CEL: wynik E7 oraz ewentualne pliki CSV do pokazu na prezentacji.
ZAKRES: scenariusz nagrań dla autora (wideo, rozmowa głosowa, przeglądanie WWW; przez VPN, jeśli jest dostępny), z czasem trwania i etykietą każdego nagrania; cechy liczone narzędziem wybranym w etapie 00, z tą samą listą kolumn co w treningu; ten sam filtr ruchu tła co w preprocess.py; porównanie rozkładów cech z danymi treningowymi przed oceną; ocena potokami z Release models-v1.
USTALENIA: repo i Releases są publiczne, a nagrania zawierają adresy IP domowej sieci i odwiedzanych serwerów. Filtr ruchu tła stosuj przed anonimizacją, potem zamień adresy na zastępcze z zachowaniem klasy multicast/broadcast, tak żeby plik przechodził kontrolę kolumn aplikacji. Na zewnątrz trafiają tylko takie pliki; PCAP-y zostają na dysku autora. Słaby wynik też jest wynikiem: raport opisze, które cechy się rozjechały i dlaczego (np. inne kodeki, QUIC, inna wersja narzędzia).
ZAPISZ: CSV w data/own/ (poza gitem) i po anonimizacji w Release own-captures-v1; reports/results/ (E7) z oznaczeniem 1–2 plików nadających się do pokazu; wynik w decyzje.md.
GOTOWE GDY: wynik E7 dla każdej usługi z komentarzem o zgodności rozkładów cech.
STOP: po scenariuszu nagrań uruchom /handoff (następna sesja zaczyna od plików w data/own/); na końcu etapu uruchom /gate od SHA startu etapu i zamknij etap (CLAUDE.md, „Praca etapami”).
```
