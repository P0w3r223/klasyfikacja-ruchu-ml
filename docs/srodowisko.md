# Środowisko pracy: komputer i laptop

| Maszyna | Rola |
| --- | --- |
| **Komputer** (ok. 1 TB wolnego miejsca) | Ciężkie etapy: przygotowanie danych, EDA, strojenie i trening modeli, ewentualnie PCAP-y (E6) |
| **Laptop** | Uruchamianie gotowych modeli i aplikacji Streamlit (np. na prezentacji) |

Duże pliki nie trafiają do historii gita. Wymiana między maszynami idzie przez **GitHub Releases**:

- `data-raw-v1`: surowy `Darknet.CSV` (zip)
- `data-processed-vN`: oczyszczony podzbiór (`.parquet`)
- `models-vN`: wytrenowane potoki (`.joblib`) i plik `models/metadata.json`

## Pierwsze uruchomienie na nowej maszynie

```bash
git clone https://github.com/P0w3r223/klasyfikacja-ruchu-ml.git
cd klasyfikacja-ruchu-ml
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
gh release download data-processed-v1 -D data/processed --skip-existing
# surowy CSV potrzebny tylko do ponownego uruchomienia src/preprocess.py:
gh release download data-raw-v1 -D data/raw --skip-existing
# potoki finalne (etap 05); metadata.json jest też w gicie
gh release download models-v1 -D models --skip-existing --pattern "*.joblib"
# kontrola: wersje, SHA-256, wczytanie i predykcja na sesjach odłożonych na pokaz
.venv\Scripts\python src/check_models.py
```

`--skip-existing` pomija pliki, które już są na dysku (np. wygenerowane lokalnie przez `preprocess.py`).
Przy przejściu na nową wersję danych (`data-processed-v2` itd.) użyj `--clobber`, żeby nadpisać stare pliki.

## Zasady przenośności modeli (żeby laptop „po prostu działał”)

1. **Ta sama wersja Pythona (3.13) i bibliotek z `requirements.txt` na obu maszynach.** Plik `.joblib` z innej wersji scikit-learn może się nie wczytać albo zachowywać inaczej.
2. Zapisujemy **cały potok** (skalowanie + model), nie sam model.
3. Obok modeli zapisujemy `metadata.json`: lista i kolejność cech, kolumny wymagane na wejściu, wersje bibliotek, SHA-256 każdego potoku, commit gita, klucze sesji odłożonych na pokaz i odsyłacz do wyniku CV z etapu 04. Wczytywanie przez `src/model_store.py`: inna wersja biblioteki, inna suma SHA-256 albo ostrzeżenie przy wczytaniu przerywa pracę.
4. Ścieżki w kodzie są względne wobec katalogu repozytorium (`pathlib`), bez `C:\Users\...`.
5. Laptop potrzebuje `models/` i kodu aplikacji. `check_models.py` potrzebuje też `data-processed-v1` (ok. 6 MB), bo sesje odłożone odnajduje w `flows.parquet`.
