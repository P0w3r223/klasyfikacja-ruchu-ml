"""Cechy przepływów jak w CICFlowMeter (Java, wersja z CIC-Darknet2020) z listy pakietów (E7).

Definicje odtworzone z kodu CICFlowMeter i sprawdzone na flows.parquet (Darknet): każda z
poniższych zależności zachodzi w 100% przepływów (docs/decyzje.md, wpis E7):
- długości to ładunek warstwy transportowej (TCP ≤ 1460 B, z rzadkimi scalonymi segmentami),
  „Header Length” to suma nagłówków TCP/UDP (UDP zawsze 8 B na pakiet);
- kierunek „Fwd” wyznacza pierwszy pakiet przepływu;
- `Packet Length Mean/Std/Variance` liczą ładunek pierwszego pakietu dwa razy (błąd w
  BasicFlow.firstPacket), `Average Packet Size` = (suma + ładunek 1. pakietu) / liczba pakietów;
- odchylenia standardowe są próbkowe (n - 1), a dla jednej wartości równe 0;
- `Fwd PSH Flags` to flaga PSH tylko pierwszego pakietu (w Darknet maksimum 1, nigdy razem z SYN);
  po timeoucie pierwszy pakiet może być „Bwd” (kierunek zostaje), wtedy 0, tak jak
  `Down/Up Ratio` przy braku pakietów Fwd;
- `Down/Up Ratio` = bwd // fwd; `Subflow *` = wartość // liczba wszystkich pakietów
  (licznik podprzepływów rośnie przy każdym pakiecie);
- „Bwd bulk” obejmuje pakiety obu kierunków (porównanie referencji tablic adresów w Javie
  kieruje każdy pakiet do gałęzi „backward”), a wyniki są obcinane do liczb całkowitych;
- przepływ kończy się po pakiecie z FIN (ten pakiet należy do przepływu) albo gdy pakiet
  przychodzi > 120 s od początku przepływu; nowy przepływ po timeoucie zachowuje kierunek starego;
- `Fwd Act Data Pkts` nie liczy pierwszego pakietu (w Darknet zawsze ≤ Total Fwd Packet − 1,
  w UDP równe mu minus 1 w 99,7% przepływów; wykryte w E6 na tych samych PCAP-ach).

Pakiety jednego połączenia podaje się jako tablice tej samej długości, posortowane po czasie:
ts (µs), payload (B ładunku), sign (+1/-1, kierunek w dowolnym stałym układzie),
header (B nagłówka TCP/UDP), flags (bity flag TCP, 0 dla UDP).
"""
from dataclasses import dataclass

import numpy as np

FLOW_TIMEOUT_US = 120_000_000
BULK_IDLE_US = 1_000_000

FIN, SYN, RST, PSH, ACK, URG = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20


@dataclass(frozen=True)
class Packets:
    ts: np.ndarray
    payload: np.ndarray
    sign: np.ndarray
    header: np.ndarray
    flags: np.ndarray

    def __len__(self) -> int:
        return len(self.ts)

    def __getitem__(self, idx) -> "Packets":
        return Packets(self.ts[idx], self.payload[idx], self.sign[idx], self.header[idx],
                       self.flags[idx])

    @staticmethod
    def of(rows: list[tuple[int, int, int, int, int]]) -> "Packets":
        """Z listy krotek (ts, payload, sign, header, flags); wygodne w testach."""
        a = np.array(rows, dtype=np.int64).reshape(-1, 5)
        return Packets(a[:, 0], a[:, 1], a[:, 2], a[:, 3], a[:, 4])


def split_flows(pk: Packets, tcp: bool) -> list[tuple[int, int, int]]:
    """Dzieli pakiety jednego połączenia na przepływy CICFlowMeter.

    Zwraca listę (początek, koniec, znak kierunku „Fwd”) jako zakresy indeksów [początek, koniec).
    Przepływ jednopakietowy zamknięty timeoutem CICFlowMeter odrzuca; tu też (taki przepływ
    i tak ma Flow Bytes/s = inf i odpada przy czyszczeniu).
    """
    ts = pk.ts.tolist()
    fin = ((pk.flags & FIN) != 0).tolist() if tcp else [False] * len(ts)
    sign = pk.sign.tolist()
    flows: list[tuple[int, int, int]] = []
    start, fsign = None, 0
    for i, t in enumerate(ts):
        if start is None:
            start, fsign = i, sign[i]
        elif t - ts[start] > FLOW_TIMEOUT_US:
            if i - start > 1:
                flows.append((start, i, fsign))
            start = i  # kierunek zostaje z poprzedniego przepływu
        elif fin[i]:
            flows.append((start, i + 1, fsign))
            start = None
    if start is not None:
        flows.append((start, len(ts), fsign))
    return flows


def _stats(x: np.ndarray) -> tuple[float, float, float, float]:
    """max, min, mean, std (próbkowe); zera dla pustej tablicy, jak w CICFlowMeter."""
    if len(x) == 0:
        return 0.0, 0.0, 0.0, 0.0
    std = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    return float(x.max()), float(x.min()), float(x.mean()), std


def _bulk(ts: np.ndarray, size: np.ndarray) -> tuple[float, float]:
    """`Bwd Packet/Bulk Avg` i `Bwd Bulk Rate Avg` (updateBackwardBulk dla wszystkich pakietów)."""
    keep = size > 0
    start = last = None
    cnt_h = 0
    states = pkts = total = duration = 0
    size_h = 0
    for t, s in zip(ts[keep].tolist(), size[keep].tolist()):
        if start is None or t - last > BULK_IDLE_US:
            start = last = t
            cnt_h, size_h = 1, s
            continue
        cnt_h += 1
        size_h += s
        if cnt_h == 4:
            states += 1
            pkts += cnt_h
            total += size_h
            duration += t - start
        elif cnt_h > 4:
            pkts += 1
            total += s
            duration += t - last
        last = t
    per_bulk = pkts // states if states else 0
    rate = int(total / (duration / 1e6)) if duration else 0
    return float(per_bulk), float(rate)


def flow_features(pk: Packets, fwd_sign: int, protocol: int) -> dict[str, float]:
    """55 cech zestawu `bez_skrotow` (models/metadata.json → features) dla jednego przepływu."""
    ts, size, hdr, flags = pk.ts, pk.payload, pk.header, pk.flags
    fwd = pk.sign == fwd_sign
    n, nf = len(pk), int(fwd.sum())
    nb = n - nf
    fs, bs = size[fwd], size[~fwd]
    F, B = int(fs.sum()), int(bs.sum())
    dur = int(ts[-1] - ts[0])
    dur_s = np.float64(dur / 1e6)

    def rate(x: int) -> float:
        """Dzielenie jak w Javie: przy zerowym czasie inf albo NaN (odpada przy czyszczeniu)."""
        with np.errstate(divide="ignore", invalid="ignore"):
            return float(np.float64(x) / dur_s)

    def count(bit: int) -> float:
        return float(((flags & bit) != 0).sum())

    fmax, fmin, fmean, fstd = _stats(fs)
    bmax, bmin, bmean, bstd = _stats(bs)
    flow_iat, fiat, biat = np.diff(ts), np.diff(ts[fwd]), np.diff(ts[~fwd])
    imax, imin, imean, istd = _stats(flow_iat)
    fimax, fimin, fimean, fistd = _stats(fiat)
    bimax, bimin, bimean, bistd = _stats(biat)
    _, _, lmean, lstd = _stats(np.concatenate([size[:1], size]))  # pierwszy pakiet dwa razy
    per_bulk, bulk_rate = _bulk(ts, size)

    return {
        "Protocol": float(protocol),
        "Flow Duration": float(dur),
        "Total Fwd Packet": float(nf),
        "Total Bwd packets": float(nb),
        "Total Length of Fwd Packet": float(F),
        "Total Length of Bwd Packet": float(B),
        "Fwd Packet Length Max": fmax, "Fwd Packet Length Min": fmin,
        "Fwd Packet Length Mean": fmean, "Fwd Packet Length Std": fstd,
        "Bwd Packet Length Max": bmax, "Bwd Packet Length Min": bmin,
        "Bwd Packet Length Mean": bmean, "Bwd Packet Length Std": bstd,
        "Flow Bytes/s": rate(F + B),
        "Flow Packets/s": rate(n),
        "Flow IAT Mean": imean, "Flow IAT Std": istd, "Flow IAT Max": imax, "Flow IAT Min": imin,
        "Fwd IAT Total": float(fiat.sum()), "Fwd IAT Mean": fimean, "Fwd IAT Std": fistd,
        "Fwd IAT Max": fimax, "Fwd IAT Min": fimin,
        "Bwd IAT Total": float(biat.sum()), "Bwd IAT Mean": bimean, "Bwd IAT Std": bistd,
        "Bwd IAT Max": bimax, "Bwd IAT Min": bimin,
        # licznik PSH rośnie tylko w firstPacket i tylko w gałęzi Fwd
        "Fwd PSH Flags": float(bool(fwd[0] and flags[0] & PSH)),
        "Fwd Header Length": float(hdr[fwd].sum()),
        "Bwd Header Length": float(hdr[~fwd].sum()),
        "Fwd Packets/s": rate(nf),
        "Bwd Packets/s": rate(nb),
        "Packet Length Min": float(size.min()),
        "Packet Length Max": float(size.max()),
        "Packet Length Mean": lmean,
        "Packet Length Std": lstd,
        "Packet Length Variance": lstd ** 2,
        "FIN Flag Count": count(FIN), "SYN Flag Count": count(SYN), "RST Flag Count": count(RST),
        "PSH Flag Count": count(PSH), "ACK Flag Count": count(ACK),
        "Down/Up Ratio": float(nb // nf) if nf else 0.0,  # Java: 0, gdy brak pakietów Fwd
        "Average Packet Size": (F + B + int(size[0])) / n,
        "Fwd Segment Size Avg": fmean,
        "Bwd Segment Size Avg": bmean,
        "Bwd Packet/Bulk Avg": per_bulk,
        "Bwd Bulk Rate Avg": bulk_rate,
        "Subflow Fwd Packets": float(nf // n),
        "Subflow Fwd Bytes": float(F // n),
        "Subflow Bwd Bytes": float(B // n),
        # firstPacket nie zwiększa licznika; w Darknet zawsze ≤ Total Fwd Packet − 1 (E6)
        "Fwd Act Data Pkts": float(((size[1:] >= 1) & fwd[1:]).sum()),
    }
