# E6, sesja 2: cechy z pierwszych N pakietów

Przepływów: 3,983. Przepływ krótszy niż N daje cechy ze wszystkich swoich pakietów, czyli takie jak pełny przepływ.

Cechy pełnego przepływu różne od e6_flows.parquet: 0 przepływów.

`obcięte`: udział przepływów dłuższych niż N (tylko w nich cechy różnią się od pełnych).

|   N | usługa   |   przepływy |   obcięte |   inf/NaN |
|----:|:---------|------------:|----------:|----------:|
|   5 | Video    |        3594 |     0.531 |         0 |
|   5 | VoIP     |         389 |     0.63  |         0 |
|  10 | Video    |        3594 |     0.289 |         0 |
|  10 | VoIP     |         389 |     0.553 |         0 |
|  20 | Video    |        3594 |     0.2   |         0 |
|  20 | VoIP     |         389 |     0.473 |         0 |
|  50 | Video    |        3594 |     0.096 |         0 |
|  50 | VoIP     |         389 |     0.365 |         0 |
