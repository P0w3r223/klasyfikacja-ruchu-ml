# Pliki do pokazu

Pliki CSV w formacie Darknet.CSV (CICFlowMeter), wejście aplikacji `app/streamlit_app.py`. Żadnego z tych przepływów modele z `models-v1` nie widziały w treningu.

| Plik | Źródło | Przepływy | Zadanie, do którego pasuje |
| --- | --- | ---: | --- |
| `darknet_tor_www_video.csv` | CIC-Darknet2020, 4 sesje odłożone (Non-Tor: WWW 12, Video 16) i 40 przepływów tła (DNS) | 68 | WWW vs Video (Tor-nonTor) |
| `darknet_vpn_voip_video.csv` | CIC-Darknet2020, 8 sesji odłożonych (NonVPN i VPN: VoIP 30, Video 25) i 48 przepływów tła (LLMNR, DNS, NetBIOS i inne) | 107 | VoIP vs Video (VPN-nonVPN) |
| `usbvpn2022_www_video.csv` | USBVPN2022 (E7): WWW 300, Video 300 | 600 | WWW vs Video |
| `usbvpn2022_voip_video.csv` | USBVPN2022 (E7): VoIP 62 (jedno spotkanie), Video 300 | 362 | VoIP vs Video |

**Darknet.** Pliki wycina `src/demo_files.py` z surowego `Darknet.CSV` (Release `data-raw-v1`, tylko komputer stacjonarny). Sesje to te odłożone w etapie 05 (`models/metadata.json` → `holdout.sessions`), a przepływy to dokładnie te, które są w `flows.parquet`. Do tego dochodzi najwyżej 10 losowych przepływów tła hostów sesji z tego samego okna czasowego na sesję, żeby było widać filtr tła. Przepływów tych hostów z innymi adresami nie bierzemy, bo należą do sesji z treningu.

**USBVPN2022.** Kopie plików z `reports/results/06_e7/demo/` (etap 06, decyzje.md 18.11). Mają zastępcze adresy IP z RFC 5737 i powtarzalne `Flow ID`, a cechy policzono starą definicją `Fwd Act Data Pkts`. Licencja CC BY 4.0 (M. Naas, J. Fesl, https://doi.org/10.5281/zenodo.7301756), zmiany opisane w głównym README.

Odtworzenie: `.venv/Scripts/python src/demo_files.py` (opcje `--raw`, `--out-dir`, `--max-background`).
