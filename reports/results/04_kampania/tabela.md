# Test kampanii: wideo z ruchu zwykłego, cel = kampania

Wygenerowane przez `src/campaign_test.py`. RF, StratifiedGroupKFold 5 po sesjach, dokładność zbalansowana (średnia ± odchylenie po foldach).

| Kampania | Przepływy | Sesje |
| --- | ---: | ---: |
| tor-nontor | 2364 | 369 |
| vpn-nonvpn | 2712 | 462 |

| Zestaw cech | Cech | Dokładność zbalansowana |
| --- | ---: | ---: |
| all | 62 | 0.997 ± 0.002 |
| bez_idle | 58 | 0.996 ± 0.002 |
| bez_skrotow | 55 | 0.982 ± 0.007 |
| bez_protocol | 57 | 0.996 ± 0.003 |
| tylko_czasowe | 15 | 0.888 ± 0.024 |
| czasowe_tempo | 20 | 0.895 ± 0.019 |
| tylko_rozmiarowe | 22 | 0.961 ± 0.019 |
