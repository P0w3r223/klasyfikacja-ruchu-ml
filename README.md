# Klasyfikacja ruchu sieciowego (WWW, VoIP, wideo) z wykorzystaniem ML

Projekt na przedmiot *Inżynieria ruchu* (Politechnika Wrocławska, 2026/27).

Cel: sprawdzić, czy na podstawie samych statystyk przepływów (bez treści pakietów) można rozpoznać usługę — przeglądanie WWW, VoIP lub wideo — także w ruchu przez VPN, oraz rzetelnie ocenić, na ile wyniki są wiarygodne (podział losowy vs. podział po sesjach).

- **Dane:** CIC-Darknet2020 (podzbiór VPN / NonVPN; Browsing, VOIP, Video-Stream)
- **Modele:** DummyClassifier (bazowy), k-NN, drzewo decyzyjne, Random Forest
- **Główna metryka:** F1 makro przy podziale grupowym (po sesjach)
- **Demo:** aplikacja Streamlit

## Struktura

```text
data/        surowe i przetworzone dane (nie w repozytorium, patrz niżej)
notebooks/   eksploracja danych i wykresy
src/         preprocess.py, train.py, evaluate.py, pcap_features.py
models/      zapisane potoki (.joblib, nie w repozytorium)
app/         streamlit_app.py
reports/     tabele wyników i rysunki do raportu
```

## Dane

Surowe dane nie są przechowywane w historii gita. Źródło: [CIC-Darknet2020 (UNB)](https://www.unb.ca/cic/datasets/darknet2020.html).
Kopia pliku `Darknet.CSV` jest w Release `data-raw-v1`:

```bash
gh release download data-raw-v1 -D data/raw
```

Pochodzenie pliku, suma kontrolna i ustalenia z przeglądu: [docs/decyzje.md](docs/decyzje.md).
Praca na dwóch maszynach (komputer i laptop): [docs/srodowisko.md](docs/srodowisko.md).

Korzystając z danych, cytuj: A. H. Lashkari, G. Kaur, A. Rahali, *DIDarknet: A Contemporary Approach to Detect and Characterize the Darknet Traffic using Deep Image Learning*, ICCNS 2020.
