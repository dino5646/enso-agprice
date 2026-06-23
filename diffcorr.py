"""diffcorr.py — 로그차분 후 시차상관 (허위상관 제거)"""
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
MAX_LAG = 12

# --- 변환: 가격은 로그차분(전월대비 변화율), ONI는 1차차분 ---
m["doni"] = m["oni"].diff()
for item in items:
    m[f"dlog_{item}"] = np.log(m[item]).diff()

print("=== 로그차분 후 시차상관 (추세·인플레이션 제거) ===")
results = {}
for item in items:
    sub = m[["doni", f"dlog_{item}"]].dropna()
    corrs = []
    for k in range(0, MAX_LAG + 1):
        x = sub["doni"].shift(k)
        pair = pd.concat([x, sub[f"dlog_{item}"]], axis=1).dropna()
        corrs.append(pair.corr().iloc[0, 1] if len(pair) > 10 else np.nan)
    results[item] = corrs
    best = int(np.nanargmax(np.abs(corrs)))
    # 대략적 유의성 기준 (n에 따른 ±2/sqrt(n))
    n = len(sub)
    thresh = 2 / np.sqrt(n)
    sig = "유의함" if abs(corrs[best]) > thresh else "유의하지 않음"
    print(f"\n[{LABELS[item]}]  (n={n}, 유의기준 |r|>{thresh:.3f})")
    print(f"  가장 강한 상관: {best}개월 시차에서 r = {corrs[best]:.3f}  → {sig}")

fig, ax = plt.subplots(figsize=(11, 6))
n = len(m.dropna(subset=["doni"]))
thresh = 2 / np.sqrt(n)
for item in items:
    ax.plot(range(0, MAX_LAG + 1), results[item], marker="o", label=LABELS[item])
ax.axhline(0, color="gray", lw=0.8)
ax.axhline(thresh, color="red", ls="--", lw=0.7, alpha=0.5)
ax.axhline(-thresh, color="red", ls="--", lw=0.7, alpha=0.5, label="유의성 기준선")
ax.set_xlabel("시차 (개월)")
ax.set_ylabel("상관계수 r (차분 후)")
ax.set_title("엘니뇨-가격 시차상관 (추세 제거 후)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
out = config.PROCESSED_DIR / "diffcorr_plot.png"
plt.savefig(out, dpi=130)
print("\n그래프 저장:", out)
