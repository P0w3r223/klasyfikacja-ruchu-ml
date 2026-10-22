# Kontekst projektu dla Claude Code

Projekt na przedmiot *Inżynieria ruchu* (Politechnika Wrocławska, telekomunikacja, V semestr, 2026/27).
Autor: Piotr Cząstkiewicz. **Komunikacja po polsku.**

## Repozytorium jest na GitHubie

- Ten folder to klon publicznego repozytorium **https://github.com/P0w3r223/klasyfikacja-ruchu-ml** (konto GitHub autora: `P0w3r223`, gałąź `main`).
- `gh` jest zalogowane jako `P0w3r223`. Po zmianach: commit, potem `git push` do `origin/main`. Przed pracą: `git pull`.
- Duże pliki (dane, modele) **nie trafiają do historii gita** (patrz `.gitignore`). Wymienia się je przez **GitHub Releases**:
  - `data-raw-v1`: `darknet2020_kaggle.zip` (surowy `Darknet.CSV`);
  - `data-processed-v1`: `flows.parquet` i `features.json`;
  - `models-vN`: wytrenowane potoki `.joblib` i `metadata.json` (jeszcze nie ma).
- Ten sam projekt jest używany na dwóch maszynach. Komputer stacjonarny (~1 TB) robi ciężkie etapy (dane, trening). Laptop ma mało miejsca, więc tylko uruchamia gotowe modele i Streamlit. Szczegóły: [docs/srodowisko.md](docs/srodowisko.md).

## Dokumenty: czytaj najpierw

| Plik | Co zawiera |
| --- | --- |
| [docs/STATUS.md](docs/STATUS.md) | **Aktualny stan**, następny krok, otwarte decyzje (nadpisywany przez `/handoff`) |
| [docs/prompty/README.md](docs/prompty/README.md) | Etapy do końca projektu: jeden prompt na etap, terminy, zależności |
| [docs/plan_projektu.md](docs/plan_projektu.md) | Pełny plan z 13.10 (sprzed EDA): pytania P1–P4, eksperymenty E1–E7, kamienie milowe |
| [docs/decyzje.md](docs/decyzje.md) | **Dziennik decyzji i ustaleń** (dane, problem kampanii, filtr tła, sesje, wyniki EDA). Aktualizuj go po każdej istotnej decyzji. |
| [docs/wstep_M1.md](docs/wstep_M1.md) | Wstęp do projektu (M1). Eksport z Claude Docs; wersja do edycji jest tam: https://claude.ai/code/artifact/f421e726-f685-4318-8004-a358f4f6921e |
| [docs/srodowisko.md](docs/srodowisko.md) | Konfiguracja obu maszyn, pobieranie z Releases, zasady przenośności modeli |
| [reports/preprocess_report.md](reports/preprocess_report.md) | Liczności po każdym kroku przygotowania danych |
| [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb) | EDA z wynikami; rysunki w `reports/figures/` |

## Stan i praca etapami

Kamienie milowe: M1 19.10.2026 (oddany), M2 16.11, M3 7.12, M4 21.12, M5 17.01.2027, M6 koniec stycznia 2027. Bieżący stan i następny krok są w [docs/STATUS.md](docs/STATUS.md), nie tutaj.

**Praca etapami:**
- Każdy etap startuje w świeżej sesji od swojego promptu z [docs/prompty/](docs/prompty/README.md). Na starcie etapu: `git pull`, potem w `docs/STATUS.md`, w sekcji Stage, linia `Etap NN od: <sha>` (`git rev-parse --short HEAD`). `/handoff` przenosi tę linię do nowego STATUS.md, dopóki etap trwa.
- Etap na kilka sesji: na końcu sesji `/handoff etap NN, czytaj docs/prompty/NN_….md`, żeby plik etapu (USTALENIA, NIE RUSZAJ, GOTOWE GDY) był w CZYTAJ następnej sesji. Potem commit i push STATUS.md i briefu; skill handoff sam nie commituje, więc to polecenie autora.
- Gdy `docs/plan_projektu.md` (13.10, sprzed EDA) różni się od `docs/decyzje.md`, obowiązuje `docs/decyzje.md`.
- Weryfikacja kodu w etapie: `/gate standard <sha startu etapu>..HEAD`. Pracujemy na `main`, więc domyślny zakres `/gate` jest pusty.
- Zamknięcie etapu: weryfikacja wskazana w prompcie → wpis w `docs/decyzje.md` → commit i push → `/handoff następny etap: docs/prompty/<plik następnego etapu>` → commit i push `docs/STATUS.md` i `.claude/sessions/`. Ten commit to polecenie autora; zastępuje sugestię `/ship` ze skilla handoff.

## Kluczowe ustalenia (szczegóły w docs/decyzje.md)

**Dane.** CIC-Darknet2020 `Darknet.CSV` z mirrora Kaggle `peterfriedrich1/cicdarknet2020-internet-traffic`.
- Wiersz 328 jest uszkodzony i pomijamy go. Zostaje 141 530 przepływów.
- Dwie kolumny nazywają się `Label` (pandas nazywa drugą `Label.1`). Pierwsza to typ ruchu, druga usługa. Pisownia etykiet jest niespójna.

**Problem kampanii.** Browsing jest tylko w Non-Tor (kampania Tor-nonTor), a VoIP tylko w VPN/NonVPN (kampania VPN-nonVPN). Nie ma VPN×Browsing.

**Wariant A** (wybrany przez autora):
- 3 klasy tylko dla ruchu zwykłego (`tunnel == "plain"`);
- E3 jako VoIP vs Video;
- Audio tylko do E5.

**Wynik EDA.** RF odróżnia kampanię na samym wideo z dokładnością zbalansowaną **0,997** (bez cech TCP 0,989). Dlatego główną miarą wiarygodności są dwa zadania wewnątrz kampanii (zaakceptowane przez prowadzącego 21.10, tak samo jak E3 dla 2 klas):
- WWW vs Video (Tor-nonTor);
- VoIP vs Video (VPN-nonVPN, w tym E3).

Podejrzane skróty: `Fwd Seg Size Min`, `Init Win Bytes`, `Idle *`. W E4 robimy wariant z nimi i bez nich.

**Ruch tła usunięty po portach.** DNS, mDNS, LLMNR, NetBIOS, SSDP, DHCP, NTP, SNMP, Dropbox, do tego multicast/broadcast oraz protokoły inne niż TCP/UDP. Porty służą tylko do filtrowania i nie są cechami modelu.

**Sesja.** Nieuporządkowana para IP + ta sama etykieta, przerwa między przepływami ≤ 5 min (`--gap-min`).

**`flows.parquet`** ma 32 441 przepływów:
- kolumny meta: `traffic_type, service, campaign, tunnel, session, ts, Src IP, Dst IP, Src Port, Dst Port`;
- 62 cechy float, których lista jest w `reports/features.json`.

**Liczności przepływów:**

| | WWW | VoIP | Video |
| --- | ---: | ---: | ---: |
| plain | 20 033 | 204 | 5 076 |
| vpn | – | 187 | 1 015 |

Audio: 5 926.

## Zasady techniczne

- Python 3.13, venv w `.venv`. Wersje bibliotek są przypięte w `requirements.txt` (sklearn 1.9.1, pandas 3.0.6) i muszą być identyczne na obu maszynach, inaczej `.joblib` może się nie wczytać.
- Zapisujemy **cały potok** (skalowanie + model) oraz `models/metadata.json`: kolejność cech, wersje, commit, wyniki.
- Ścieżki względne przez `ROOT = Path(__file__).resolve().parents[1]`, bez `C:\Users\...`.
- Ładowanie danych: `from features import load_flows, feature_list, feature_groups` (z katalogu `src`).
- Nowe dane lub modele idą do nowego Release (`gh release create ...`), nie do gita. Pobieranie z `--skip-existing`, a przy nowej wersji z `--clobber`.
- Na Windows przy polskich znakach w konsoli: `PYTHONIOENCODING=utf-8`.
- Testy: `.venv/Scripts/python -m pytest -q` (`pytest.ini` dodaje `src` do ścieżki). Odtworzenie danych bez nadpisywania repo: `src/preprocess.py --raw … --out-dir … --reports-dir …`.
- Pandas 3: `groupby(...).apply` gubi kolumnę grupującą. Do próbkowania per grupa używaj `pd.concat([... for _, g in df.groupby(...)])`. `Series.to_numpy()` zwraca tablicę tylko do odczytu, więc przed modyfikacją `to_numpy(copy=True)`.
- `StratifiedGroupKFold` wyrównuje udział przepływów, nie sesji: gdy jedna sesja ma więcej niż 1/n_outer przepływów klasy, jej fold dostaje tylko ją i `evaluate.py` przerywa przebieg. Przed nowym zadaniem sprawdź udział największej sesji (VoIP: 30% w ruchu zwykłym); obejście to mniej foldów w `experiments.py` (decyzja autora, jak w 03b).
- Commity po polsku.
- Dokumenty w `docs/` (także `docs/research/`) i `reports/` piszemy po polsku; to wyjątek od globalnej reguły knowledge-docs, bo raport i prezentacja są po polsku.
