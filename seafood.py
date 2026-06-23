"""seafood.py — 수산물 ENSO 분석 + 온난화 구분 (ONI vs RONI vs 추세통제)"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

import config

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

fish = {"mackerel":"고등어","squid":"오징어","hairtail":"갈치"}
sub = prices[prices["name"].isin(fish)]
wide = sub.pivot_table(index="date", columns="name", values="price").reset_index()

df = enso[["date","oni","roni"]].merge(wide, on="date", how="inner").sort_values("date").reset_index(drop=True)
df["d_oni"]=df["oni"].diff()
df["d_roni"]=df["roni"].diff()
df["t"]=range(len(df))            # 시간추세
df["month"]=df["date"].dt.month
for f in fish:
    df[f"d_{f}"]=np.log(df[f]).diff()

def best_lag(fishkey, xvar, add_trend=False):
    """시차 0~6 중 가장 유의한 결과 반환"""
    best=(None,1.0,None)
    for lag in range(0,7):
        d=df.copy(); d["x"]=d[xvar].shift(lag)
        need=[f"d_{fishkey}","x"]
        d=d.dropna(subset=need)
        formula=f"d_{fishkey} ~ x + C(month)" + (" + t" if add_trend else "")
        m=smf.ols(formula,data=d).fit()
        if m.pvalues["x"] < best[1]:
            best=(lag, m.pvalues["x"], m.params["x"])
    return best

print("="*70)
print("  수산물 ENSO 효과: ONI vs RONI vs 추세통제  (최강 시차 기준)")
print("="*70)
print(f"  {'품목':>6} | {'ONI':>22} | {'RONI(온난화제거)':>22} | {'ONI+추세통제':>20}")
print(f"  {'':>6} | {'시차 계수 p값':>22} | {'시차 계수 p값':>22} | {'시차 계수 p값':>20}")
print("-"*70)
for fk, fn in fish.items():
    o=best_lag(fk,"d_oni")
    r=best_lag(fk,"d_roni")
    tr=best_lag(fk,"d_oni",add_trend=True)
    def fmt(b):
        s = "**" if b[1]<0.05 else ("*" if b[1]<0.10 else " ")
        return f"{b[0]}월 {b[2]:+.3f} {b[1]:.3f}{s}"
    print(f"  {fn:>6} | {fmt(o):>22} | {fmt(r):>22} | {fmt(tr):>20}")

print("-"*70)
print("  ** p<0.05, * p<0.10")
print("  해석: ONI와 RONI 둘 다 유의 → 온난화 아닌 진짜 ENSO 효과")
print("        ONI만 유의, RONI 무효 → 온난화 추세였을 가능성")
