"""contrast_plot.py — 한국 vs 글로벌 시차별 ENSO 효과 대비 그래프"""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from matplotlib import font_manager

import config

try:
    font_manager.fontManager.addfont("C:/Windows/Fonts/malgun.ttf")
    matplotlib.rc("font", family="Malgun Gothic")
except Exception:
    pass
matplotlib.rcParams["axes.unicode_minus"] = False

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
wb = pd.read_csv(config.PROCESSED_DIR / "worldbank_commodities.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

# 한국 품목
cab = prices[prices["name"].str.startswith("cabbage")].groupby("date")["price"].mean().reset_index()
cab["name"]="cabbage"
chili = prices[prices["name"]=="Dried_chili"][["date","price"]].copy(); chili["name"]="chili"
kor = pd.concat([cab,chili]).pivot_table(index="date",columns="name",values="price").reset_index()

df = enso[["date","oni"]].merge(wb,on="date",how="inner").merge(kor,on="date",how="left").sort_values("date").reset_index(drop=True)
df["d_oni"]=df["oni"].diff()
df["d_crude"]=np.log(df["crude_oil"]).diff()

targets = {
    "sugar":"설탕(글로벌)","soybean":"대두(글로벌)","maize":"옥수수(글로벌)","wheat":"밀(글로벌)",
    "cabbage":"배추(한국)","chili":"건고추(한국)",
}
for c in targets:
    df[f"d_{c}"]=np.log(df[c]).diff()

MAXLAG=6
def coefs(crop):
    cs=[]
    for lag in range(MAXLAG+1):
        d=df.copy(); d["dol"]=d["d_oni"].shift(lag)
        d["month"]=d["date"].dt.month
        sub=d.dropna(subset=[f"d_{crop}","dol","d_crude"])
        m=smf.ols(f"d_{crop} ~ dol + d_crude + C(month)",data=sub).fit()
        cs.append((m.params["dol"], m.pvalues["dol"]))
    return cs

fig, ax = plt.subplots(figsize=(12,7))
colors={"sugar":"#d62728","soybean":"#ff7f0e","maize":"#bcbd22","wheat":"#8c564b",
        "cabbage":"#1f77b4","chili":"#17becf"}
for crop,label in targets.items():
    cs=coefs(crop)
    coef=[c[0] for c in cs]; pval=[c[1] for c in cs]
    is_kor = crop in ("cabbage","chili")
    ax.plot(range(MAXLAG+1), coef, marker="o",
            color=colors[crop], label=label,
            lw=2.5 if not is_kor else 1.5,
            ls="-" if not is_kor else "--",
            alpha=0.9 if not is_kor else 0.6)
    # 유의한 점(p<0.05) 강조
    for lag,(cf,pv) in enumerate(cs):
        if pv<0.05:
            ax.plot(lag, cf, marker="*", color=colors[crop], markersize=16, zorder=5)

ax.axhline(0,color="gray",lw=1)
ax.set_xlabel("시차 (개월): 엘니뇨 발생 후 경과 개월")
ax.set_ylabel("ENSO 계수 (가격 변화율에 대한 영향)")
ax.set_title("ENSO의 가격 영향: 글로벌 곡물(실선) vs 한국 채소(점선)\n★ = 통계적으로 유의 (p<0.05)")
ax.legend(loc="lower left", ncol=2)
ax.grid(alpha=0.3)
plt.tight_layout()
out=config.PROCESSED_DIR / "contrast_plot.png"
plt.savefig(out,dpi=140)
print("저장:",out)
