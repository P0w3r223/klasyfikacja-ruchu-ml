# Klasyfikacja ruchu sieciowego (WWW, VoIP, wideo) z wykorzystaniem ML

Projekt na przedmiot *Inżynieria ruchu* (Politechnika Wrocławska, 2026/27).

Cel: sprawdzić, czy na podstawie samych statystyk przepływów (bez treści pakietów) można rozpoznać usługę: przeglądanie WWW, VoIP lub wideo, także w ruchu przez VPN. Drugim celem jest rzetelna ocena, na ile te wyniki są wiarygodne (podział losowy vs podział po sesjach, skróty w cechach, zbiór zewnętrzny).

- **Dane:** CIC-Darknet2020 (ruch Non-Tor, NonVPN i VPN; Browsing, VOIP, Video-Streaming). Ograniczenia zbioru i zmiana zakresu: [docs/decyzje.md](docs/decyzje.md).
- **Test zewnętrzny (E7):** USBVPN2022, ruch z innego laboratorium i z innego roku, tylko do oceny.
- **Modele:** DummyClassifier (bazowy), k-NN, drzewo decyzyjne, Random Forest.
- **Główna metryka:** F1 makro przy podziale po sesjach, na zestawie cech bez skrótów (`bez_skrotow`, 55 cech).
- **Demo:** aplikacja Streamlit (etap 09, w przygotowaniu).

Aktualny stan i następny krok: [docs/STATUS.md](docs/STATUS.md). Wyniki i decyzje: [docs/decyzje.md](docs/decyzje.md). Etapy do końca projektu: [docs/prompty/README.md](docs/prompty/README.md).

## Struktura

```text
data/        surowe i przetworzone dane, data/external/ (USBVPN2022); poza gitem, patrz niżej
notebooks/   01_eda.ipynb (eksploracja danych)
src/         przygotowanie danych: preprocess.py, features.py
             ocena i eksperymenty: evaluate.py, models.py, experiments.py, train.py, importance.py
             modele finalne: finalize.py, model_store.py, check_models.py, e5_audio.py
             E7: usbvpn.py, cic_features.py, e7.py, e7_ocena.py, darknet_csv.py
             rysunki: make_figures_*.py, make_eda_notebook.py
tests/       pytest
models/      metadata.json (w gicie) i potoki .joblib (Release models-v1)
reports/     results/ (wyniki przebiegów), figures/ (rysunki), raport postępów
docs/        plan, decyzje, stan, środowisko, prompty etapów, przegląd źródeł i literatury
app/         aplikacja Streamlit (etap 09)
```

## Dane i modele (GitHub Releases)

Duże pliki nie są w historii gita. Wymienia się je przez Releases:

| Release | Zawartość | Katalog |
| --- | --- | --- |
| `data-raw-v1` | `darknet2020_kaggle.zip` (surowy `Darknet.CSV`) | `data/raw/` |
| `data-processed-v1` | `flows.parquet`, `features.json` | `data/processed/` |
| `models-v1` | 9 potoków `.joblib` (k-NN, drzewo, RF × 3 zadania) i `metadata.json` | `models/` |
| `usbvpn-processed-v1` | `usbvpn_flows.parquet` (przepływy z USBVPN2022 do E7) | `data/external/` |

Przykład: `gh release download models-v1 -D models --skip-existing --pattern "*.joblib"`. Konfiguracja obu maszyn, pełna lista poleceń i zasady przenośności modeli: [docs/srodowisko.md](docs/srodowisko.md).

## Uruchomienie

Python 3.13, wersje bibliotek przypięte w `requirements.txt`. Muszą być identyczne jak przy treningu, inaczej `.joblib` się nie wczyta.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest -q                       # testy
.venv/Scripts/python src/check_models.py                # kontrola potoków z models-v1
.venv/Scripts/python src/train.py --experiment <nazwa>  # eksperyment z rejestru src/experiments.py
.venv/Scripts/python src/e7.py ocena                    # E7: potoki na USBVPN2022
```

Na Windows przy polskich znakach w konsoli ustaw `PYTHONIOENCODING=utf-8`.

## Źródła danych i licencje

**CIC-Darknet2020:** [UNB](https://www.unb.ca/cic/datasets/darknet2020.html), kopia z Kaggle (`peterfriedrich1/cicdarknet2020-internet-traffic`). Korzystając z danych, cytuj: A. H. Lashkari, G. Kaur, A. Rahali, *DIDarknet: A Contemporary Approach to Detect and Characterize the Darknet Traffic using Deep Image Learning*, ICCNS 2020.

**USBVPN2022:** M. Naas, J. Fesl, *Encrypted VPN Dataset*, Zenodo, https://doi.org/10.5281/zenodo.7301756; artykuł: Data in Brief 2023, https://pmc.ncbi.nlm.nih.gov/articles/PMC9925847/. Licencja [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). `usbvpn_flows.parquet` i pliki w `reports/results/06_e7/demo/` to utwory zależne, udostępniane na tej samej licencji. Zmiany względem oryginału:
- z rekordów pmacct policzono przepływy i cechy według definicji CICFlowMeter;
- usunięto ruch tła i infrastruktury;
- scalone segmenty TCP rozbito na segmenty MSS;
- w plikach demo dodano zastępcze adresy IP (RFC 5737).
