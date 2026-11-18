# USBVPN2022: część VPN (tylko liczności, E7)

Pliki `VPN/<typ>/<usługa>.json`, bez filtra ruchu tła i infrastruktury. Połączenie = protokół + para portów (brak adresów IP). „Największe połączenie” to jego udział we wpisach `x_packets` pliku.

| VPN | usługa | rekordy | wpisy x_packets | połączenia | połączenia ≥ 100 wpisów | największe połączenie | jego udział | 2 największe |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| L2TP | Video | 112 | 1,042,122 | 2 | 1 | udp/1701/1701 | 100.0% | 100.0% |
| L2TP IPsec | Video | 182 | 1,240,407 | 2 | 2 | udp/4500/4500 | 100.0% | 100.0% |
| OpenVPN | Video | 98 | 960,200 | 1 | 1 | tcp/1194/47774 | 100.0% | 100.0% |
| PPTP | Video | 145 | 3,336,470 | 2 | 2 | gre/0/0 | 100.0% | 100.0% |
| SSTP | Video | 97 | 964,234 | 1 | 1 | tcp/443/52538 | 100.0% | 100.0% |
| WireGuard | Video | 190 | 1,484,564 | 2 | 2 | udp/13231/31026 | 100.0% | 100.0% |
| L2TP | VoIP | 2 | 28,134 | 1 | 1 | udp/1701/1701 | 100.0% | 100.0% |
| L2TP IPsec | VoIP | 4 | 81,981 | 2 | 1 | udp/4500/4500 | 100.0% | 100.0% |
| OpenVPN | VoIP | 2 | 46,104 | 1 | 1 | tcp/1194/47774 | 100.0% | 100.0% |
| PPTP | VoIP | 2 | 36,430 | 2 | 1 | gre/0/0 | 100.0% | 100.0% |
| SSTP | VoIP | 2 | 67,121 | 1 | 1 | tcp/443/52538 | 100.0% | 100.0% |
| WireGuard | VoIP | 3 | 34,031 | 2 | 1 | udp/13231/31026 | 100.0% | 100.0% |
| L2TP | WWW | 1,194 | 7,731,013 | 2 | 2 | udp/1701/1701 | 100.0% | 100.0% |
| L2TP IPsec | WWW | 1,759 | 12,435,430 | 3 | 3 | udp/4500/4500 | 99.9% | 100.0% |
| OpenVPN | WWW | 1,010 | 6,159,330 | 1 | 1 | tcp/1194/47774 | 100.0% | 100.0% |
| PPTP | WWW | 1,361 | 8,705,989 | 4 | 4 | gre/0/0 | 98.5% | 99.9% |
| SSTP | WWW | 1,009 | 7,881,432 | 1 | 1 | tcp/443/52538 | 100.0% | 100.0% |
| WireGuard | WWW | 1,555 | 12,227,556 | 2 | 2 | udp/13231/31026 | 100.0% | 100.0% |
