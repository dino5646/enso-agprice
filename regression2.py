"""regression2.py — 환율 통제 + 시차 ONI 회귀"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

import config

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])
wb = pd.read_csv(config.PROCESSED_DIR / "worldbank_commodities.csv", parse_dates=["date"])
fx = pd.read_csv(config.PROCESSED_DIR / "usdkrw.csv", parse_dates=["date"])

cab = prices[prices["name"].str.startswith("cabbage")].groupby("date")["price"].mean().reset_index()
cab["name"] = "cabbage"
chili = prices[prices["name"] == "Dried_chili"][["date", "price"]].copy()
chili["name"] = "chili"
allp = pd.concat([cab, chili], ignore_index=True)
wide = allp.pivot_table(index="date", columns="name", values="price").reset_index()

df = enso[["date", "oni"]].merge(wide, on="date", how="inner")
df = df.merge(wb[["date", "crude_oil", "wheat"]], on="date", how="left")
df = df.merge(fx[["date", "usdkrw"]], on="date", how="left")
df = df.sort_values("date").reset_index(drop=True)

for col in ["cabbage", "chili", "crude_oil", "wheat", "usdkrw"]:
    df[f"d_{col}"] = np.log(df[col]).diff()
df["d_oni"] = df["oni"].diff()
df["month"] = df["date"].dt.month

def run(target, lag):
    d = df.copy()
    d["d_oni_lag"] = d["d_oni"].shift(lag)
    need = [f"d_{target}", "d_oni_lag", "d_crude_oil", "d_wheat", "d_usdkrw"]
    sub = d.dropna(subset=need).copy()
    formula = f"d_{target} ~ d_oni_lag + d_crude_oil + d_wheat + d_usdkrw + C(month)"
    model = smf.ols(formula, data=sub).fit()
    coef = model.params["d_oni_lag"]
    pval = model.pvalues["d_oni_lag"]
    return coef, pval, model.rsquared, int(model.nobs)

for target in ["cabbage", "chili"]:
    print(f"\n{'='*60}")
    print(f"  {target} — 환율 통제 + 시차별 ENSO 효과")
    print(f"{'='*60}")
    print(f"  {'시차':>4} {'ENSO계수':>10} {'p-value':>9} {'유의':>6} {'R^2':>6}")
    for lag in range(0, 4):
        coef, pval, r2, n = run(target, lag)
        sig = "**" if pval < 0.05 else ("*" if pval < 0.10 else "")
        print(f"  {lag:>3}월 {coef:>10.4f} {pval:>9.4f} {sig:>6} {r2:>6.3f}")
    print(f"  (n={n})")

print("\n* p<0.10, ** p<0.05")
