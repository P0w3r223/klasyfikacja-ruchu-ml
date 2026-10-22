# Etap 09: aplikacja Streamlit (M5)

```text
KONTEKST: Etap 09, kamień M5. Aplikacja posłuży do ok. 3-minutowego pokazu na prezentacji, uruchamianego na laptopie. Złożoność MEDIUM, bez @architect (decyzja autora): kontrakt modeli jest ustalony w metadata.json z etapu 05.
CZYTAJ: docs/STATUS.md, docs/plan_projektu.md §6.1, models/metadata.json
CEL: działająca aplikacja app/streamlit_app.py i zestaw plików CSV do pokazu.
ZAKRES: funkcje z planu §6.1 (wgranie CSV, kontrola kolumn według metadata.json, wybór zadania i modelu spośród zapisanych w metadata.json, klasy przepływów, rozkład klas, najważniejsze cechy; macierz pomyłek i F1, gdy plik ma etykiety); pliki do pokazu w app/demo/ wycięte z surowego Darknet.CSV po kluczach sesji odłożonych w etapie 05 (flows.parquet nie ma kolumn Label ani Timestamp, więc nie nadaje się na wejście), plus ewentualnie pliki z E7, wyłącznie w wersji zanonimizowanej (repo jest publiczne).
USTALENIA: wejście to CSV w formacie Darknet.CSV. Aplikacja stosuje ten sam filtr ruchu tła co preprocess.py, bo inaczej przepływy DNS czy LLMNR dostaną etykietę jednej z trzech usług. Kolejność cech pochodzi z metadata.json, a dane przechodzą przez ten sam potok co w treningu; plik bez wymaganych kolumn dostaje komunikat, której kolumny brakuje. Pokaz działa bez internetu, a pliki demo mają najwyżej kilka MB, bo trafiają do repo.
ZAPISZ: app/, app/demo/, instrukcja uruchomienia w README.md.
GOTOWE GDY: na laptopie, w czystym klonie, po pobraniu models-v1 `streamlit run` działa, a każdy plik demo daje wynik w kilka sekund.
STOP: pokaż wynik uruchomienia, uruchom /gate od SHA startu etapu; potem zamknij etap (CLAUDE.md, „Praca etapami”).
```
