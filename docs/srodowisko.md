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
```

`--skip-existing` pomija pliki, które już są na dysku (np. wygenerowane lokalnie przez `preprocess.py`).
Przy przejściu na nową wersję danych (`data-processed-v2` itd.) użyj `--clobber`, żeby nadpisać stare pliki.

## Zasady przenośności modeli (żeby laptop „po prostu działał”)

1. **Ta sama wersja Pythona (3.13) i bibliotek z `requirements.txt` na obu maszynach.** Plik `.joblib` z innej wersji scikit-learn może się nie wczytać albo zachowywać inaczej.
2. Zapisujemy **cały potok** (skalowanie + model), nie sam model.
3. Obok modeli zapisujemy `metadata.json`: lista i kolejność cech wejściowych, wersje bibliotek, data, commit gita i wyniki na teście. Aplikacja sprawdza go przy starcie.
4. Ścieżki w kodzie są względne wobec katalogu repozytorium (`pathlib`), bez `C:\Users\...`.
5. Laptop potrzebuje tylko `models/` i kodu aplikacji. Nie trzeba na nim trzymać danych treningowych.
