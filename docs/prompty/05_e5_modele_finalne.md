# Etap 05: E5 i finalne modele (zamyka M4)

Dla autora: ostatni krok (sprawdzenie na laptopie) wymaga przesiadki. Na PC: `/handoff etap 05, czytaj docs/prompty/05_e5_modele_finalne.md`, potem commit i push. Na laptopie: `git pull` i wklej prompt, który wypisał `/handoff`.

```text
KONTEKST: Etap 05, zamyka M4. Powstają potoki dla aplikacji (etap 09) i test kontrolny E5. Od tego etapu zależą E7, aplikacja i pokaz na prezentacji.
CZYTAJ: docs/STATUS.md, docs/decyzje.md (wyniki E2–E4), docs/plan_projektu.md §6.1
CEL: potoki w Release models-v1, działające na obu maszynach, sesje odłożone na pokaz oraz wynik E5.
ZAKRES: propozycja, które zadania obsługuje aplikacja i jak je opisać; dla każdego z nich 2–3 sesje odłożone na pokaz, opisane w models/metadata.json trwałym kluczem (etykieta, para IP, zakres ts), bo numer w kolumnie session zmienia się przy innej wersji danych lub progu; potoki k-NN, drzewa i RF (plan §6.1) uczone bez tych sesji; w metadata.json także zestaw cech (z cechami-skrótami czy bez, decyzja na podstawie E4), lista kolumn wymaganych na wejściu aplikacji, wersja Release danych i próg sesji; E5: przepływy Audio przez finalny model 3-klasowy i rozkład przewidzianych klas; Release models-v1; sprawdzenie wczytania i predykcji na laptopie.
USTALENIA: konfigurację potoków wybieraj po wynikach walidacji wewnętrznej, nie po wynikach na danych testowych; raportowany wynik pochodzi z etapów 03b–04. Audio występuje w obu kampaniach i w VPN, a model 3-klasowy uczono tylko na ruchu zwykłym, więc wynik E5 rozbij na kampanię i tunel.
ZAPISZ: reports/results/ (E5), models/metadata.json, Release models-v1, wybór zadań i modeli dla aplikacji oraz wynik E5 w decyzje.md.
GOTOWE GDY: na laptopie, w czystym klonie, po pobraniu models-v1 krótki skrypt wczytuje każdy potok i przewiduje na odłożonych sesjach bez błędów i bez ostrzeżeń o wersjach.
STOP: najpierw pokaż propozycję zadań dla aplikacji i zapytaj autora; na końcu pokaż wynik E5, uruchom /gate od SHA startu etapu i zamknij etap (CLAUDE.md, „Praca etapami”).
```
