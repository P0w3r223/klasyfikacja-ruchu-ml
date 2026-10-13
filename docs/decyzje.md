# Dziennik decyzji i ustaleń

## 2026-10-13: Źródło danych

- **Plik:** `Darknet.CSV`, 73 325 208 B, SHA-256 `3E89B9747841C44401FDCEEEA18B0FD3932F7A38F53D15A47395872CBAC18433`
- **Skąd:** kopia na Kaggle `peterfriedrich1/cicdarknet2020-internet-traffic` (wgrana 2020-09-25). Oficjalne źródło (UNB, http://cicresearch.ca/CICDataset/CICDarknet2020/) wymaga formularza rejestracyjnego. Rozmiar zgadza się z plikiem z serwera UNB (73,33 MB).
- **Licencja:** UNB pozwala na redystrybucję w dowolnej formie pod warunkiem cytowania: Lashkari, Kaur, Rahali, *DIDarknet…*, ICCNS 2020.
- **Kopia w projekcie:** GitHub Release `data-raw-v1`.
- **TODO:** porównać SHA-256 z plikiem pobranym z UNB (formularz wypełnia autor).

## 2026-10-13: Wstępny przegląd (`src/inspect_raw.py`)

- Wiersz 328 jest uszkodzony: dwa ucięte przepływy rozdzielone ~8 MB bajtów zerowych. Pomijamy go. Zostaje **141 530 przepływów**, tyle samo co w literaturze.
- Dwie kolumny nazywają się `Label`. Pierwsza to typ ruchu (Tor / Non-Tor / VPN / NonVPN), druga usługa.
- Etykiety usług mają niespójną pisownię: `Video-Streaming` / `Video-streaming`, `Audio-Streaming` / `AUDIO-STREAMING`, `File-Transfer` / `File-transfer`. Trzeba je ujednolicić.
- 49 wierszy z inf, 47 z NaN, 15 kolumn stałych (m.in. wszystkie `Active *`), 24 457 pełnych duplikatów i 38 361 duplikatów po usunięciu IP, portów i czasu.

### Liczności w zakresie projektu (po ujednoliceniu etykiet)

| Typ ruchu | Browsing | VOIP | Video-Streaming |
| --- | ---: | ---: | ---: |
| NonVPN | **0** | 2 101 | 5 039 |
| VPN | **0** | 1 167 | 1 144 |
| Non-Tor | 32 545 | **0** | 3 382 |

### Problem: Browsing i VoIP nie występują w tej samej kampanii pomiarowej

- **Browsing** jest tylko w ruchu Non-Tor (kampania ISCX Tor-nonTor: sieć 10.152.x przez bramę Whonix, lipiec 2015 i luty 2016).
- **VoIP** jest tylko w ruchu VPN / NonVPN (kampania ISCX VPN-nonVPN: sieć 131.202.x lub tunel 10.8.x, marzec–czerwiec 2015).
- Skutek 1: brakuje kombinacji VPN × Browsing, więc eksperyment E3 dla trzech klas nie jest wykonalny na samym CIC-Darknet2020.
- Skutek 2: klasa WWW jest doskonale skorelowana z kampanią pomiarową (inna sieć, inny sprzęt, inne daty). Model może uczyć się rozpoznawać kampanię zamiast usługi.
- VoIP to mało sesji: 69 par IP i 18 źródłowych IP (NonVPN), 51 par i 12 IP (VPN), każda kampania z jednego dnia. To ma znaczenie dla GroupKFold.
- Wideo występuje w obu kampaniach (Non-Tor i NonVPN), więc pozwala zmierzyć, jak silny jest efekt kampanii.

**Decyzja:** do podjęcia (warianty w odpowiedzi z 2026-10-13; skonsultować z prowadzącym).
