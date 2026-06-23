"""regression.py — ENSO 다중회귀 (통제변수: 유가, 밀, 계절)"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

import config

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])
wb = pd.read_csv(config.PROCESSED_DIR / "worldbank_commodities.csv", parse_dates=["date"])

# 배추 4종 통합(월평균) + 건고추
cab = prices[prices["name"].str.startswith("cabbage")].groupby("date")["price"].mean().reset_index()
cab["name"] = "cabbage"
chili = prices[prices["name"] == "Dried_chili"][["date", "price"]].copy()
chili["name"] = "chili"
allp = pd.concat([cab, chili], ignore_index=True)
wide = allp.pivot_table(index="date", columns="name", values="price").reset_index()

# 병합
df = enso[["date", "oni"]].merge(wide, on="date", how="inner")
df = df.merge(wb[["date", "crude_oil", "wheat"]], on="date", how="left")
df = df.sort_values("date").reset_index(drop=True)

# 로그차분 (추세·인플레 제거)
for col in ["cabbage", "chili", "crude_oil", "wheat"]:
    df[f"d_{col}"] = np.log(df[col]).diff()
df["d_oni"] = df["oni"].diff()
df["month"] = df["date"].dt.month  # 계절 통제용

def run(target):
    sub = df.dropna(subset=[f"d_{target}", "d_oni", "d_crude_oil", "d_wheat"]).copy()
    # 계절 더미 + 통제변수 + ENSO
    formula = f"d_{target} ~ d_oni + d_crude_oil + d_wheat + C(month)"
    model = smf.ols(formula, data=sub).fit()
    print(f"\n{'='*55}")
    print(f"  종속변수: {target} 가격 변화율  (n={int(model.nobs)})")
    print(f"{'='*55}")
    # ENSO 계수만 핵심 출력
    coef = model.params["d_oni"]
    pval = model.pvalues["d_oni"]
    sig = "유의함 ***" if pval < 0.05 else ("약하게 유의 *" if pval < 0.10 else "유의하지 않음")
    print(f"  ENSO(d_oni) 계수: {coef:.4f}")
    print(f"  p-value: {pval:.4f}  → {sig}")
    print(f"  모델 설명력 R^2: {model.rsquared:.3f}")
    print(f"\n  [전체 계수표]")
    print(model.summary().tables[1])

for t in ["cabbage", "chili"]:
    run(t)

print("\n해석: ENSO 계수의 p<0.05 면 '다른 변수 통제 후에도 ENSO 효과 있음'")
