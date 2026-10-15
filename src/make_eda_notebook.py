"""Generuje notebooks/01_eda.ipynb (bez wyników).

Użycie: python src/make_eda_notebook.py notebooks/01_eda.ipynb
Potem: jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb
"""
import sys
import nbformat as nbf

out = sys.argv[1]
nb = nbf.v4.new_notebook()
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md("""
# 01 – Eksploracyjna analiza danych (EDA)

Podzbiór CIC-Darknet2020 po `src/preprocess.py` (wariant A): usługi WWW, VoIP, Video, ruch zwykły (Non-Tor + NonVPN) i VPN.
Dane: `data/processed/flows.parquet` (Release `data-processed-v1`).

Pytania tego notatnika:
1. Ile mamy przepływów i sesji w każdej kombinacji?
2. Czym różnią się usługi w kluczowych cechach i które grupy cech niosą najwięcej informacji (wstęp do P1)?
3. Które cechy są nadmiarowe (silnie skorelowane)?
4. **Jak silny jest efekt kampanii pomiarowej?** WWW pochodzi z innej kampanii niż VoIP; wideo jest w obu, więc pozwala to zmierzyć.
5. Jak VPN zmienia rozkłady cech VoIP i wideo (wstęp do P3)?
""")

code("""
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
while not (ROOT / "src").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ks_2samp
from sklearn.feature_selection import mutual_info_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold, cross_val_score

from features import SERVICES, feature_groups, feature_group, feature_list, load_flows

FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
SEED = 42
PALETTE = {"WWW": "#4C72B0", "VoIP": "#DD8452", "Video": "#55A868"}
sns.set_theme(style="whitegrid", context="notebook")
pd.set_option("display.width", 160)

df = load_flows()
FEATURES = feature_list()
GROUPS = feature_groups(FEATURES)
plain = df[df["tunnel"] == "plain"]
print(f"{len(df):,} przepływów, {len(FEATURES)} cech")
{g: len(f) for g, f in GROUPS.items()}
""")

md("## 1. Liczności przepływów i sesji")

code("""
counts = df.groupby(["tunnel", "traffic_type", "service"]).agg(
    przeplywy=("session", "size"), sesje=("session", "nunique"))
counts["przeplywy_na_sesje"] = (counts["przeplywy"] / counts["sesje"]).round(1)
counts
""")

code("""
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, col, title in zip(axes, ["przeplywy", "sesje"], ["Przepływy", "Sesje"]):
    t = counts[col].groupby(["tunnel", "service"]).sum().unstack("service").reindex(columns=SERVICES)
    t.plot.bar(ax=ax, color=[PALETTE[s] for s in SERVICES], rot=0)
    ax.set_yscale("log"); ax.set_title(f"{title} (skala log)"); ax.set_xlabel("")
    for c in ax.containers:
        ax.bar_label(c, fmt="%d", fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "01_licznosci.png", dpi=150)
""")

md("""
## 2. Wielkość sesji

Przy podziale grupowym duże sesje ważą najwięcej: jedna sesja z 30% przepływów klasy przesądza o wyniku foldu.
""")

code("""
sess = df.groupby(["service", "tunnel", "session"]).size().rename("n").reset_index()
fig, ax = plt.subplots(figsize=(8, 3.8))
sns.boxplot(data=sess, x="service", y="n", hue="tunnel", order=SERVICES, ax=ax, log_scale=True)
ax.set_ylabel("przepływy w sesji (log)"); ax.set_xlabel("")
fig.tight_layout(); fig.savefig(FIG / "02_wielkosc_sesji.png", dpi=150)
sess.groupby(["service", "tunnel"])["n"].describe(percentiles=[.5, .9, .99]).round(1)
""")

md("""
## 3. Rozkłady kluczowych cech – ruch zwykły

Cechy mają rozkłady o długich ogonach, więc pokazuję log10(1 + x). Czasy w CICFlowMeter są w mikrosekundach.
""")

code("""
KEY = ["Average Packet Size", "Packet Length Std", "Flow Bytes/s", "Flow Packets/s",
       "Flow IAT Mean", "Flow Duration", "Total Fwd Packet", "Down/Up Ratio"]
long = plain.melt(id_vars="service", value_vars=KEY, var_name="cecha", value_name="v")
long["log10(1+x)"] = np.log10(1 + long["v"].clip(lower=0))
g = sns.catplot(data=long, x="service", y="log10(1+x)", col="cecha", col_wrap=4, kind="box",
                order=SERVICES, palette=PALETTE, hue="service", sharey=False, height=2.8, showfliers=False)
g.set_titles("{col_name}"); g.set_xlabels("")
g.figure.savefig(FIG / "03_kluczowe_cechy.png", dpi=150)
""")

code("""
summary = plain.groupby("service")[KEY].median().T.reindex(columns=SERVICES)
summary["udział UDP"] = np.nan
udp = plain.groupby("service")["Protocol"].apply(lambda s: (s == 17).mean())
print("Udział UDP:", udp.reindex(SERVICES).round(2).to_dict())
summary.drop(columns="udział UDP").round(1)
""")

md("""
## 4. Informacyjność pojedynczych cech (wstęp do P1)

Informacja wzajemna (mutual information) każdej cechy z usługą, osobno dla ruchu zwykłego.
To miara jednowymiarowa: nie widzi interakcji cech, więc jest tylko wstępem do E4.
""")

code("""
sample = pd.concat([g.sample(min(len(g), 5000), random_state=SEED)
                    for _, g in plain.groupby("service")])
mi = pd.Series(mutual_info_classif(sample[FEATURES], sample["service"], random_state=SEED),
               index=FEATURES, name="MI").sort_values(ascending=False)
mi_df = mi.to_frame().assign(grupa=[feature_group(f) for f in mi.index])

fig, ax = plt.subplots(figsize=(8, 6))
top = mi_df.head(25).iloc[::-1]
gcol = dict(zip(GROUPS, sns.color_palette("Set2", len(GROUPS))))
ax.barh(top.index, top["MI"], color=[gcol[g] for g in top["grupa"]])
for g, c in gcol.items():
    ax.barh([], [], color=c, label=g)
ax.legend(title="grupa", loc="lower right"); ax.set_xlabel("informacja wzajemna z usługą [nat]")
ax.set_title("25 najbardziej informacyjnych cech – ruch zwykły")
fig.tight_layout(); fig.savefig(FIG / "04_informacja_wzajemna.png", dpi=150)

mi_df.groupby("grupa")["MI"].agg(["count", "mean", "max"]).sort_values("max", ascending=False).round(3)
""")

md("""
## 5. Korelacje i nadmiarowość cech

Wiele cech CICFlowMeter to warianty tej samej wielkości (np. `Packet Length Std` i `Variance`, `Subflow Fwd Bytes` i `Total Length of Fwd Packet`).
Dla drzew to nie problem, ale k-NN liczy odległość, więc nadmiarowe cechy zwielokrotniają wagę jednej informacji.
""")

code("""
corr = plain[FEATURES].corr(method="spearman").fillna(0)
cg = sns.clustermap(corr, cmap="vlag", center=0, figsize=(13, 13), xticklabels=True, yticklabels=True,
                    cbar_pos=(0.02, 0.85, 0.02, 0.1))
cg.ax_heatmap.tick_params(labelsize=6)
cg.figure.savefig(FIG / "05_korelacje.png", dpi=150)
plt.close(cg.figure)

upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack()
high = upper[upper.abs() >= 0.98].sort_values(ascending=False)
print(f"Pary cech o |rho Spearmana| >= 0.98: {len(high)}")
high.head(20).round(3)
""")

md("""
## 6. Efekt kampanii pomiarowej

WWW występuje tylko w kampanii Tor-nonTor, VoIP tylko w VPN-nonVPN. Wideo jest w obu, więc porównanie
**wideo z kampanii Tor-nonTor vs wideo z kampanii VPN-nonVPN** pokazuje, ile różnicy wnosi sama kampania przy tej samej usłudze.

Dla każdej cechy liczę statystykę Kołmogorowa–Smirnowa (0 = identyczne rozkłady, 1 = rozłączne):
- **efekt kampanii:** wideo Non-Tor vs wideo NonVPN,
- **efekt usługi:** WWW vs wideo w tej samej kampanii (Non-Tor).

Cechy, w których efekt kampanii dorównuje efektowi usługi, są podejrzane jako „skróty”.
""")

code("""
vid = plain[plain["service"] == "Video"]
v_tor = vid[vid["campaign"] == "tor-nontor"]
v_vpn = vid[vid["campaign"] == "vpn-nonvpn"]
www = plain[plain["service"] == "WWW"]

ks = pd.DataFrame({
    "kampania (wideo)": [ks_2samp(v_tor[f], v_vpn[f]).statistic for f in FEATURES],
    "usługa (WWW vs wideo)": [ks_2samp(www[f], v_tor[f]).statistic for f in FEATURES],
}, index=FEATURES)
ks["grupa"] = [feature_group(f) for f in FEATURES]

fig, ax = plt.subplots(figsize=(7, 6))
for g, sub in ks.groupby("grupa"):
    ax.scatter(sub["usługa (WWW vs wideo)"], sub["kampania (wideo)"], label=g, color=gcol[g], s=30)
ax.plot([0, 1], [0, 1], ls="--", c="grey", lw=1)
for f, r in ks.nlargest(6, "kampania (wideo)").iterrows():
    ax.annotate(f, (r["usługa (WWW vs wideo)"], r["kampania (wideo)"]), fontsize=7,
                xytext=(4, 2), textcoords="offset points")
ax.set_xlabel("KS: efekt usługi (WWW vs wideo, ta sama kampania)")
ax.set_ylabel("KS: efekt kampanii (wideo vs wideo)")
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(title="grupa", fontsize=8)
ax.set_title("Cechy powyżej przekątnej mocniej mówią o kampanii niż o usłudze")
fig.tight_layout(); fig.savefig(FIG / "06_efekt_kampanii.png", dpi=150)

ks.sort_values("kampania (wideo)", ascending=False).head(12).round(2)
""")

md("Początkowe okno TCP zależy od systemu operacyjnego i konfiguracji hosta. Najczęstsze wartości w każdej kombinacji:")

code("""
def top_values(s, k=3):
    vc = s.value_counts(normalize=True).head(k)
    return ", ".join(f"{int(v)} ({p:.0%})" for v, p in vc.items())

tcp = df[df["Protocol"] == 6]
tcp.groupby(["campaign", "tunnel", "service"]).agg(
    fwd_init_win=("FWD Init Win Bytes", top_values),
    bwd_init_win=("Bwd Init Win Bytes", top_values))
""")

md("""
### Wstępny test: czy model odróżnia kampanię przy tej samej usłudze?

Random Forest uczy się przewidywać **kampanię** na samych przepływach wideo (podział grupowy po sesjach, 5 foldów, zbalansowana dokładność).
0,5 = kampanii nie da się odróżnić, 1,0 = kampania jest w pełni rozpoznawalna. To zapowiedź testu kontrolnego z M4, nie jego ostateczna wersja.
""")

code("""
cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
rf = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=SEED, class_weight="balanced")
variants = {
    "wszystkie cechy": FEATURES,
    "bez TCP/protokołu": [f for f in FEATURES if feature_group(f) != "tcp_protokol"],
    "tylko czasowe": GROUPS["czasowe"],
    "tylko rozmiarowe": GROUPS["rozmiarowe"],
}
camp = {}
for name, cols in variants.items():
    s = cross_val_score(rf, vid[cols], vid["campaign"], groups=vid["session"], cv=cv,
                        scoring="balanced_accuracy")
    camp[name] = (s.mean(), s.std())
pd.DataFrame(camp, index=["zbalansowana dokładność", "odch. std"]).T.round(3)
""")

md("## 7. Ruch zwykły vs VPN (VoIP i wideo, kampania VPN-nonVPN)")

code("""
vv = df[(df["campaign"] == "vpn-nonvpn") & df["service"].isin(["VoIP", "Video"])]
long = vv.melt(id_vars=["service", "tunnel"], value_vars=KEY, var_name="cecha", value_name="v")
long["log10(1+x)"] = np.log10(1 + long["v"].clip(lower=0))
g = sns.catplot(data=long, x="service", y="log10(1+x)", hue="tunnel", col="cecha", col_wrap=4,
                kind="box", sharey=False, height=2.8, showfliers=False, order=["VoIP", "Video"])
g.set_titles("{col_name}"); g.set_xlabels("")
g.figure.savefig(FIG / "07_vpn_vs_zwykly.png", dpi=150)
""")

code("""
ks_vpn = pd.DataFrame({
    s: [ks_2samp(vv.loc[(vv.service == s) & (vv.tunnel == "plain"), f],
                 vv.loc[(vv.service == s) & (vv.tunnel == "vpn"), f]).statistic for f in FEATURES]
    for s in ["VoIP", "Video"]}, index=FEATURES)
ks_vpn["VoIP vs Video (zwykły)"] = [
    ks_2samp(vv.loc[(vv.service == "VoIP") & (vv.tunnel == "plain"), f],
             vv.loc[(vv.service == "Video") & (vv.tunnel == "plain"), f]).statistic for f in FEATURES]
ks_vpn["grupa"] = [feature_group(f) for f in FEATURES]
print("Średni KS w grupach: zmiana od VPN (VoIP, Video) vs różnica między usługami")
ks_vpn.groupby("grupa").mean(numeric_only=True).round(2)
""")

md("## 8. Wnioski")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, out)
