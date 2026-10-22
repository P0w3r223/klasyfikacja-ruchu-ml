# Etapy projektu: prompty do kolejnych sesji

Date: 2026-10-22
Status: proposed
Author: Piotr Cząstkiewicz + Claude
Related to: docs/plan_projektu.md, docs/decyzje.md, docs/STATUS.md

---

Każdy plik to jeden etap pracy do końca semestru. Etap zaczyna się w świeżej sesji Claude Code od wklejenia bloku `text` z pliku etapu.

## Jak używać

1. Nowa sesja w katalogu repo (CLAUDE.md wczytuje się sam), `git pull`, potem wklej prompt etapu.
2. Etap na kilka sesji: na końcu sesji `/handoff etap NN, czytaj docs/prompty/NN_….md`, potem commit i push. W następnej sesji (także na drugiej maszynie, po `git pull`) wklej prompt, który on wypisał.
3. Start, weryfikację i zamknięcie etapu opisuje CLAUDE.md, sekcja „Praca etapami”.
4. Linia „Dla autora” w pliku etapu to rzeczy, które robisz sam (formularze, nagrania, pomiar czasu).

## Etapy

Terminy, maszyny i liczba sesji są tylko w tej tabeli; przy przesunięciu terminu poprawiamy jedno miejsce.

| # | Etap | Termin | Maszyna | Sesje | Zależy od | Weryfikacja |
| --- | --- | --- | --- | --- | --- | --- |
| [00](00_weryfikacja_zrodel.md) | Weryfikacja źródeł, zamienniki, go/no-go E6 | 25.10.2026 | dowolna | 1–2 | – | dostępność i licencje sprawdzone u źródła |
| [01](01_literatura.md) | Przegląd literatury | 2.11.2026 | dowolna | 1–2 | 00 | liczby i cytaty sprawdzone w tekście źródła |
| [02](02_weryfikacja_danych.md) | Weryfikacja danych i testy przygotowania (zamyka M2) | 9.11.2026 | PC | 1–2 | 00 | pytest, `/gate` |
| [03a](03a_modul_treningu.md) | Moduł treningu i schemat oceny (M3, cz. 1) | 23.11.2026 | PC | 2 | 02 | pytest, `/gate` |
| [03b](03b_e1_e2.md) | E1/E2: podział losowy vs po sesjach (M3) | 7.12.2026 | PC | 1–2 | 03a | `/gate` |
| [04](04_e3_e4.md) | E3 (VPN) i E4 (ważność cech) | 18.12.2026 | PC | 2 | 03b | `/gate` |
| [05](05_e5_modele_finalne.md) | E5 i finalne modele (zamyka M4) | 21.12.2026 | PC, potem laptop | 2 | 04 | wczytanie na laptopie, `/gate` |
| [06](06_e7_wlasne_przechwycenia.md) | E7: własne przechwycenia | przerwa świąteczna | laptop + PC | 2 | 00, 05 | zgodność rozkładów cech, `/gate` |
| [07](07_e6_wczesna_klasyfikacja.md) | E6: wczesna klasyfikacja (tylko przy „go” z 00; **22.10: no-go z warunkiem powrotu**, docs/decyzje.md) | 6.01.2027 | PC | 1–2 | 00, 03a | `/gate` |
| [08](08_wyniki.md) | Zestawienie wyników | 10.01.2027 | PC | 1 | 03b–07 | rysunki odtwarzalne skryptem, `/gate` |
| [09](09_streamlit.md) | Aplikacja Streamlit (M5) | 17.01.2027 | PC + laptop | 1–2 | 05 | uruchomienie na laptopie, `/gate` |
| [10](10_dokumentacja.md) | Dokumentacja | 20.01.2027 | PC | 1 | 09 | subagent wykonuje README dosłownie |
| [11](11_raport.md) | Raport pisemny (M6) | 26.01.2027 | dowolna | 2–3 | 01, 08 | `/recenzja` ≥ 7/10 |
| [12](12_prezentacja.md) | Prezentacja 10 min (M6) | 28.01.2027 | dowolna | 2 | 08, 09 | `/recenzja` ≥ 7/10 |
| [13](13_proba_generalna.md) | Próba generalna | przed prezentacją | laptop | 1 | 12 | lista kontrolna przechodzi na laptopie |

Przy opóźnieniach jako pierwszy odpada etap 07 (E6), potem 06 (E7).

## Jak są napisane prompty

- Format jest ten sam co prompt z `/handoff` (KONTEKST, CZYTAJ, CEL, ZAKRES, NIE RUSZAJ, GOTOWE GDY, STOP), rozszerzony o USTALENIA i ZAPISZ.
- Prompty nie powtarzają CLAUDE.md, planu ani wiedzy ogólnej (metryki, potoki sklearn). Wskazują, co przeczytać, i zawierają tylko ustalenia specyficzne dla projektu.
- Złożoność według planning.md: 03a LARGE (z @architect); 07 i 09 MEDIUM mimo nowego modułu (decyzja autora); pozostałe etapy z kodem MEDIUM.
- Gdy zmienia się decyzja, poprawiamy `docs/decyzje.md`. Prompt poprawiamy tylko wtedy, gdy zmienia się cel albo zakres etapu.
- Wersja z 22.10 uwzględnia recenzję agenta `critic` (6/10): zakres `/gate` na `main`, przekazanie stanu między sesjami, kontrakt modeli dla aplikacji, osiągalne kryteria ukończenia, scalenie E3+E4, podział etapu 03, ocena E6 w etapie 00.
