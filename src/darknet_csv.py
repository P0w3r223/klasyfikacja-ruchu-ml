"""Przepływy z innych źródeł zapisane w formacie Darknet.CSV (wejście aplikacji, etap 09).

Zapisujemy tylko kolumny, które mamy: identyfikatory przepływu, 55 cech z kontraktu
(`metadata.json` → `features`) i dwie kolumny `Label`. Kolumn, których nie liczymy (skróty
`Idle *`, `Init Win Bytes`, cechy stałe), nie wypełniamy wymyślonymi wartościami.
"""
import pandas as pd

ID_COLS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Protocol", "Timestamp"]
TIMESTAMP_FORMAT = "%d/%m/%Y %I:%M:%S %p"  # jak w Darknet.CSV i preprocess.py
SERVICE_LABELS = {"WWW": "Browsing", "Video": "Video-Streaming", "VoIP": "VOIP"}
# Adresy zastępcze z bloków dokumentacyjnych RFC 5737: nie są ruchem tła (multicast, .255)
# ani prawdziwymi hostami. USBVPN2022 nie ma adresów IP.
PLACEHOLDER_SRC_IP, PLACEHOLDER_DST_IP = "192.0.2.10", "198.51.100.10"


def to_darknet_frame(flows: pd.DataFrame, features: list[str],
                     traffic_type: str) -> pd.DataFrame:
    """Ramka z kolumnami w kolejności Darknet.CSV; obie kolumny etykiet nazywają się `Label`.

    `flows` musi mieć `service`, `ts`, `Src Port`, `Dst Port` i wszystkie `features`.
    """
    unknown = sorted(set(flows["service"]) - set(SERVICE_LABELS))
    if unknown:
        raise ValueError(f"Brak pisowni Darknet dla usług {unknown}")
    ports = flows[["Src Port", "Dst Port"]].astype(int)
    proto = flows["Protocol"].astype(int)
    ids = pd.DataFrame({
        "Flow ID": (PLACEHOLDER_SRC_IP + "-" + PLACEHOLDER_DST_IP + "-"
                    + ports["Src Port"].astype(str) + "-" + ports["Dst Port"].astype(str)
                    + "-" + proto.astype(str)),
        "Src IP": PLACEHOLDER_SRC_IP, "Src Port": ports["Src Port"],
        "Dst IP": PLACEHOLDER_DST_IP, "Dst Port": ports["Dst Port"], "Protocol": proto,
        "Timestamp": pd.to_datetime(flows["ts"]).dt.strftime(TIMESTAMP_FORMAT)},
        index=flows.index)
    rest = [f for f in features if f != "Protocol"]
    labels = pd.DataFrame({"traffic": traffic_type,
                           "service": flows["service"].map(SERVICE_LABELS)}, index=flows.index)
    out = pd.concat([ids, flows[rest], labels], axis=1).reset_index(drop=True)
    out.columns = [*ID_COLS, *rest, "Label", "Label"]
    return out


def sample_per_service(flows: pd.DataFrame, n_per_service: dict[str, int],
                       seed: int) -> pd.DataFrame:
    """Losowe przepływy każdej usługi (wszystkie, gdy jest ich mniej), posortowane po czasie."""
    parts = []
    for service, n in n_per_service.items():
        g = flows[flows["service"] == service]
        if g.empty:
            raise ValueError(f"Brak przepływów usługi {service}")
        parts.append(g.sample(n=min(n, len(g)), random_state=seed))
    return pd.concat(parts).sort_values("ts", kind="stable")
