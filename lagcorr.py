"""lagcorr.py — ENSO(ONI)와 가격의 시차상관 분석"""
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

LABELS = {"Napa_cabbage_fall": "배추(가을)", "Dried_chili": "건고추"}

m = pd.read_csv(config.PROCESSED_DIR / "merged_analysis.csv", parse_dates=["date"])
m = m.sort_values("date").reset_index(drop=True)

items = [c for c in LABELS if c in m.columns]
MAX_LAG = 12  # 0~12개월 시차

print("=== 시차상관 (ONI가 k개월 앞설 때 가격과의 상관계수) ===")
results = {}
for item in items:
    sub = m[["oni", item]].dropna()
    corrs = []
    for k in range(0, MAX_LAG + 1):
        # ONI를 k개월 시프트 → k개월 뒤 가격과 비교
        x = sub["oni"].shift(k)
        pair = pd.concat([x, sub[item]], axis=1).dropna()
        if len(pair) > 10:
            corrs.append(pair.corr().iloc[0, 1])
        else:
            corrs.append(np.nan)
    results[item] = corrs
    best_lag = int(np.nanargmax(np.abs(corrs)))
    print(f"\n[{LABELS[item]}]")
    print(f"  가장 강한 상관: {best_lag}개월 시차에서 r = {corrs[best_lag]:.3f}")
    print(f"  (양수=엘니뇨 때 가격↑, 음수=엘니뇨 때 가격↓)")

# 그래프
fig, ax = plt.subplots(figsize=(11, 6))
for item in items:
    ax.plot(range(0, MAX_LAG + 1), results[item], marker="o", label=LABELS[item])
ax.axhline(0, color="gray", lw=0.8)
ax.set_xlabel("시차 (개월): ONI가 가격보다 몇 개월 앞서는가")
ax.set_ylabel("상관계수 r")
ax.set_title("엘니뇨(ONI) - 농산물 가격 시차상관")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
out = config.PROCESSED_DIR / "lagcorr_plot.png"
plt.savefig(out, dpi=130)
print("\n그래프 저장:", out)
