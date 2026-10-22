# Etap 07: E6, wczesna klasyfikacja (tylko przy decyzji „go”)

Dla autora: uruchom ten etap tylko wtedy, gdy w etapie 00 zapadła decyzja „go” dla E6. Przy „no-go” pomijasz go.

```text
KONTEKST: Etap 07, opcjonalny. W etapie 00 autor zdecydował „go” dla E6 (docs/decyzje.md, docs/research/zrodla.md, sekcja „E6: go/no-go”). Złożoność MEDIUM, bez @architect (decyzja autora).
CZYTAJ: docs/STATUS.md, docs/research/zrodla.md (sekcja E6), docs/plan_projektu.md §2 (P4)
CEL: odpowiedź na P4: ile pierwszych pakietów przepływu wystarcza do rozpoznania usługi.
ZAKRES: pobranie PCAP-ów wskazanych w etapie 00; src/pcap_features.py liczący cechy z pierwszych N pakietów (N = 5, 10, 20, 50) i z pełnego przepływu; eksperyment modułem z etapu 03a, podział po sesjach.
USTALENIA: własny skrypt nie odtworzy cech CICFlowMeter, więc punkt odniesienia „pełny przepływ” liczy ten sam skrypt, a nie bierzemy go z E2. PCAP-y zostają poza gitem. Jeśli w trakcie okaże się, że nakład wyraźnie przekracza ocenę z etapu 00, zatrzymaj się i zapytaj autora, czy kończymy jako „no-go”.
ZAPISZ: src/pcap_features.py z testami, reports/results/ (E6), rysunek w reports/figures/, odpowiedź na P4 w decyzje.md.
GOTOWE GDY: wykres F1 makro w funkcji N z punktem odniesienia dla pełnego przepływu i odpowiedź na P4.
STOP: pokaż wykres i odpowiedź na P4, uruchom /gate od SHA startu etapu; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
