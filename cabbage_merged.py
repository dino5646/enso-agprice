"""cabbage_merged.py — 배추 4계절 통합 후 차분 시차상관"""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib import font_manager

import config

try:
    font_manager.fontManager.addfont("C:/Windows/Fonts/malgun.ttf")
    matplotlib.rc("font", family="Malgun Gothic")
except Exception:
    pass
matplotlib.rcParams["axes.unicode_minus"] = False

enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

# 배추 4종을 같은 달 평균으로 통합
cab = prices[prices["name"].str.startswith("cabbage")].copy()
cab_m = cab.groupby("date")["price"].mean().reset_index()
cab_m["name"] = "배추통합"

chili = prices[prices["name"] == "Dried_chili"].copy()
chili["name"] = "건고추"

allp = pd.concat([cab_m, chili[["date", "price", "name"]]], ignore_index=True)
wide = allp.pivot_table(index="date", columns="name", values="price")
m = enso.merge(wide, on="date", how="inner").sort_values("date").reset_index(drop=True)

items = ["배추통합", "건고추"]
MAX_LAG = 12
m["doni"] = m["oni"].diff()
for it in items:
    m[f"d_{it}"] = np.log(m[it]).diff()

print("=== 배추 4계절 통합 후 차분 시차상관 ===")
results = {}
for it in items:
    sub = m[["doni", f"d_{it}"]].dropna()
    corrs = []
    for k in range(MAX_LAG + 1):
        x = sub["doni"].shift(k)
        pair = pd.concat([x, sub[f"d_{it}"]], axis=1).dropna()
        corrs.append(pair.corr().iloc[0, 1] if len(pair) > 10 else np.nan)
    results[it] = corrs
    best = int(np.nanargmax(np.abs(corrs)))
    n = len(sub)
    thresh = 2 / np.sqrt(n)
    sig = "유의함" if abs(corrs[best]) > thresh else "유의하지 않음"
    print(f"\n[{it}]  (n={n}, 유의기준 |r|>{thresh:.3f})")
    print(f"  최강 상관: {best}개월 시차 r = {corrs[best]:.3f}  → {sig}")

fig, ax = plt.subplots(figsize=(11, 6))
for it in items:
    ax.plot(range(MAX_LAG + 1), results[it], marker="o", label=it)
ax.axhline(0, color="gray", lw=0.8)
ax.set_xlabel("시차 (개월)")
ax.set_ylabel("상관계수 r (차분 후)")
ax.set_title("엘니뇨-가격 시차상관 (배추 4계절 통합, 추세 제거)")
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
out = config.PROCESSED_DIR / "cabbage_merged_plot.png"
plt.savefig(out, dpi=130)
print("\n그래프 저장:", out)
print("배추통합 기간:", m.dropna(subset=['배추통합']).date.min().date(), "~", m.dropna(subset=['배추통합']).date.max().date())
