"""regime.py — 강한 ENSO 국면에서만 가격 반응 보기"""
import pandas as pd
import numpy as np

import config

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

cab = prices[prices["name"].str.startswith("cabbage")].groupby("date")["price"].mean().reset_index()
cab["name"] = "배추"
chili = prices[prices["name"] == "Dried_chili"][["date", "price"]].copy()
chili["name"] = "건고추"
allp = pd.concat([cab, chili], ignore_index=True)
wide = allp.pivot_table(index="date", columns="name", values="price").reset_index()

m = enso[["date", "oni", "phase"]].merge(wide, on="date", how="inner").sort_values("date").reset_index(drop=True)
for it in ["배추", "건고추"]:
    m[f"d_{it}"] = np.log(m[it]).diff()  # 전월대비 변화율

# 강도 구분
def regime(o):
    if o >= 1.0: return "강한 엘니뇨"
    if o >= 0.5: return "약한 엘니뇨"
    if o <= -1.0: return "강한 라니냐"
    if o <= -0.5: return "약한 라니냐"
    return "중립"
m["regime"] = m["oni"].map(regime)

order = ["강한 라니냐", "약한 라니냐", "중립", "약한 엘니뇨", "강한 엘니뇨"]
for it in ["배추", "건고추"]:
    print(f"\n{'='*55}")
    print(f"  {it}: ENSO 국면별 평균 월간 가격변화율")
    print(f"{'='*55}")
    print(f"  {'국면':>10} {'개월수':>6} {'평균변화율':>10} {'표준편차':>9}")
    for r in order:
        g = m[m["regime"] == r][f"d_{it}"].dropna()
        if len(g) > 0:
            print(f"  {r:>10} {len(g):>6} {g.mean()*100:>9.2f}% {g.std()*100:>8.2f}%")

# 강한 엘니뇨 vs 강한 라니냐 t검정
from scipy import stats
print(f"\n{'='*55}")
print("  강한 엘니뇨 vs 강한 라니냐 (가격변화율 차이 검정)")
print(f"{'='*55}")
for it in ["배추", "건고추"]:
    el = m[m["regime"]=="강한 엘니뇨"][f"d_{it}"].dropna()
    la = m[m["regime"]=="강한 라니냐"][f"d_{it}"].dropna()
    if len(el)>2 and len(la)>2:
        t, p = stats.ttest_ind(el, la, equal_var=False)
        sig = "유의함**" if p<0.05 else ("약하게*" if p<0.10 else "유의하지않음")
        print(f"  {it}: 엘니뇨평균 {el.mean()*100:+.2f}% vs 라니냐평균 {la.mean()*100:+.2f}%  p={p:.3f} {sig}")
