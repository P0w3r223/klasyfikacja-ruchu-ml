"""Wstępny przegląd surowego pliku Darknet.CSV (kroki 1-2 przed modelowaniem).

Użycie: python src/inspect_raw.py data/raw/Darknet.CSV
"""
import sys

import numpy as np
import pandas as pd

path = sys.argv[1]
# Wiersz 328 jest uszkodzony (dwa ucięte przepływy sklejone ~8 MB bajtów zerowych) - pomijamy go.
df = pd.read_csv(path, low_memory=False, on_bad_lines="warn")

# Dwie kolumny mają nazwę "Label"; pandas zmienia drugą na "Label.1".
df = df.rename(columns={"Label": "traffic_type", "Label.1": "service"})

print(f"Wiersze: {len(df):,}  kolumny: {df.shape[1]}")
print("\n== Typ ruchu ==")
print(df["traffic_type"].value_counts(dropna=False).to_string())
print("\n== Usługa (surowe wartości) ==")
print(df["service"].value_counts(dropna=False).to_string())
print("\n== Typ ruchu x usługa ==")
print(pd.crosstab(df["service"], df["traffic_type"], margins=True).to_string())

num = df.select_dtypes(include=[np.number])
print(f"\nKolumny nienumeryczne: {[c for c in df.columns if c not in num.columns]}")
print(f"Wiersze z inf: {np.isinf(num).any(axis=1).sum():,}")
print(f"Wiersze z NaN: {df.isna().any(axis=1).sum():,}")
const = [c for c in num.columns if num[c].nunique(dropna=False) <= 1]
print(f"Kolumny stałe ({len(const)}): {const}")
feat = df.drop(columns=["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp"])
print(f"Pełne duplikaty wierszy: {df.duplicated().sum():,}")
print(f"Duplikaty po usunięciu IP/portów/czasu: {feat.duplicated().sum():,}")

ts = pd.to_datetime(df["Timestamp"], format="%d/%m/%Y %I:%M:%S %p", errors="coerce")
print(f"\nNieparsowalne znaczniki czasu: {ts.isna().sum():,}")
df["date"] = ts.dt.date
print("\n== Daty przechwyceń x typ ruchu ==")
print(pd.crosstab(df["date"], df["traffic_type"]).to_string())

df["pair"] = df["Src IP"] + "<->" + df["Dst IP"]
sub = df[df["traffic_type"].isin(["VPN", "NonVPN", "Non-Tor"])]
print("\n== Liczba unikalnych par IP i źródłowych IP na kombinację ==")
print(sub.groupby(["traffic_type", "service"]).agg(
    flows=("pair", "size"), ip_pairs=("pair", "nunique"),
    src_ips=("Src IP", "nunique"), days=("date", "nunique")).to_string())
