# USBVPN2022 → przepływy CICFlowMeter (E7)

Źródło: Naas, Fesl, „Encrypted VPN Dataset” (USBVPN2022), Zenodo 10.5281/zenodo.7301756, licencja CC BY 4.0. Tylko pliki `Non VPN`.

Scalone segmenty TCP: bez zmian.

## non_streaming.json → WWW

- rekordy pmacct: 46,191; usunięte filtrem: 8,410; połączenia (protokół + porty): 20,744 (scalono 17,037 rekordów)
- wpisy x_packets: 4,864,617, w tym z packets > 1: 34,654; pakiety z ujemnym ładunkiem (ustawione na 0): 265; scalone segmenty TCP: 0 (→ 0 pakietów)
- przepływy CICFlowMeter: 45,312; inf/NaN: 1,597; duplikaty: 918; **zostaje 42,797**

| powód usunięcia | rekordy | wpisy x_packets |
| --- | ---: | ---: |
| protokół inny niż TCP/UDP | 3,433 | 8,212,886 |
| infrastruktura TCP/8291 (Winbox) | 1,529 | 503,721 |
| infrastruktura TCP/10443 | 1,400 | 2,800 |
| infrastruktura UDP/9000 | 1,013 | 3,537,050 |
| infrastruktura UDP/13231 (WireGuard MikroTik) | 996 | 2,541 |
| NTP | 15 | 30 |
| NetBIOS | 14 | 14 |
| DNS | 6 | 12 |
| SSDP | 3 | 3 |
| mDNS | 1 | 1 |

## streaming.json → Video

- rekordy pmacct: 3,807; usunięte filtrem: 1,033; połączenia (protokół + porty): 2,524 (scalono 250 rekordów)
- wpisy x_packets: 741,996, w tym z packets > 1: 31,745; pakiety z ujemnym ładunkiem (ustawione na 0): 38; scalone segmenty TCP: 0 (→ 0 pakietów)
- przepływy CICFlowMeter: 3,198; inf/NaN: 263; duplikaty: 21; **zostaje 2,914**

| powód usunięcia | rekordy | wpisy x_packets |
| --- | ---: | ---: |
| protokół inny niż TCP/UDP | 456 | 1,004,858 |
| infrastruktura TCP/10443 | 370 | 740 |
| infrastruktura UDP/9000 | 91 | 475,876 |
| infrastruktura UDP/13231 (WireGuard MikroTik) | 91 | 687 |
| infrastruktura TCP/8291 (Winbox) | 15 | 31,457 |
| NTP | 5 | 10 |
| NetBIOS | 4 | 4 |
| DHCP | 1 | 2 |

## meet.json → VoIP

- rekordy pmacct: 72; usunięte filtrem: 21; połączenia (protokół + porty): 51 (scalono 0 rekordów)
- wpisy x_packets: 18,130, w tym z packets > 1: 138; pakiety z ujemnym ładunkiem (ustawione na 0): 0; scalone segmenty TCP: 0 (→ 0 pakietów)
- przepływy CICFlowMeter: 67; inf/NaN: 5; duplikaty: 0; **zostaje 62**

| powód usunięcia | rekordy | wpisy x_packets |
| --- | ---: | ---: |
| infrastruktura TCP/10443 | 13 | 26 |
| protokół inny niż TCP/UDP | 4 | 21,641 |
| infrastruktura UDP/9000 | 2 | 10,637 |
| infrastruktura UDP/13231 (WireGuard MikroTik) | 1 | 24 |
| NTP | 1 | 2 |
