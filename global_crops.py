"""global_crops.py — 글로벌 열대작물 ENSO 시차회귀"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

import config

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
wb = pd.read_csv(config.PROCESSED_DIR / "worldbank_commodities.csv", parse_dates=["date"])

df = enso[["date", "oni"]].merge(wb, on="date", how="inner").sort_values("date").reset_index(drop=True)

crops = ["sugar", "soybean", "wheat", "maize"]
df["d_oni"] = df["oni"].diff()
df["d_crude"] = np.log(df["crude_oil"]).diff()
for c in crops:
    df[f"d_{c}"] = np.log(df[c]).diff()
df["month"] = df["date"].dt.month

print("=== 글로벌 작물: 시차별 ENSO 효과 (유가·계절 통제) ===")
for crop in crops:
    print(f"\n[{crop}]")
    print(f"  {'시차':>4} {'ENSO계수':>10} {'p-value':>9} {'유의':>5}")
    best_p = 1.0
    for lag in range(0, 7):
        d = df.copy()
        d["d_oni_lag"] = d["d_oni"].shift(lag)
        sub = d.dropna(subset=[f"d_{crop}", "d_oni_lag", "d_crude"])
        model = smf.ols(f"d_{crop} ~ d_oni_lag + d_crude + C(month)", data=sub).fit()
        coef = model.params["d_oni_lag"]
        pval = model.pvalues["d_oni_lag"]
        sig = "**" if pval<0.05 else ("*" if pval<0.10 else "")
        mark = " <-- 최강" if pval < best_p else ""
        if pval < best_p: best_p = pval
        print(f"  {lag:>3}월 {coef:>10.4f} {pval:>9.4f} {sig:>5}{mark}")

print("\n* p<0.10, ** p<0.05")
print("한국 배추·고추는 어떤 시차에서도 유의X 였음 → 비교 포인트")
