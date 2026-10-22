# Etap 03a: moduł treningu i schemat oceny (M3, część 1)

```text
KONTEKST: Etap 03a, pierwsza część M3. Powstaje nowy moduł treningu i oceny (src/train.py, src/evaluate.py), na którym stoją etapy 03b–05. Złożoność LARGE według planning.md: najpierw @architect (struktura modułu i schemat oceny), akceptacja autora, potem plan i implementacja.
CZYTAJ: docs/STATUS.md, docs/plan_projektu.md §5, docs/decyzje.md (od wpisu „EDA – efekt kampanii”)
CEL: przetestowany moduł z uzasadnionym schematem oceny, sprawdzony od początku do końca na jednym zadaniu.
ZAKRES: moduł przyjmuje konfigurację: zadanie, podzbiór treningowy i testowy, zestaw cech, model (Dummy, k-NN, drzewo, RF), podział (losowy stratyfikowany albo po kolumnie session); strojenie hiperparametrów tylko na części treningowej; wyniki per fold zapisywane maszynowo (CSV/JSON w reports/results/). Zdefiniowane trzy zadania: 3 usługi w ruchu zwykłym (punkt odniesienia); WWW vs Video w kampanii Tor-nonTor; VoIP vs Video w kampanii VPN-nonVPN, ruch zwykły i VPN razem. Pilotaż: VoIP vs Video, 4 modele, oba podziały.
USTALENIA: VoIP ma 25–49 sesji, a największa z nich zawiera ok. 30% przepływów, więc rozrzut między foldami jest równie ważny jak średnia. Schemat oceny (np. hold-out testowy vs zagnieżdżona CV) i sposób wyboru konfiguracji bez użycia danych testowych dobierz do tej liczby sesji. Etap 03b sprawdzi próg sesji 15 min: moduł ma umożliwić przeliczenie sesji w pamięci (assign_sessions na kolumnach flows.parquet), bo preprocess.py z innym --gap-min nadpisuje dane i raport. E3–E5 będą tylko zmieniać konfigurację.
NIE RUSZAJ: data/processed/ ani src/preprocess.py; to dane wejściowe wszystkich kolejnych etapów.
ZAPISZ: src/train.py, src/evaluate.py, testy, schemat oceny z uzasadnieniem w decyzje.md, wyniki pilotażu w reports/results/.
GOTOWE GDY: pytest przechodzi; jedno polecenie odtwarza wyniki pilotażu; autor zaakceptował schemat oceny.
STOP: pokaż wyniki pilotażu, uruchom /gate od SHA startu etapu; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
