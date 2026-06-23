"""analyze.py — ENSO와 농산물 가격 결합 + 첫 시각화"""
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

import config

# 한글 폰트 (윈도우 맑은 고딕)
try:
    font_manager.fontManager.addfont("C:/Windows/Fonts/malgun.ttf")
    matplotlib.rc("font", family="Malgun Gothic")
except Exception:
    pass
matplotlib.rcParams["axes.unicode_minus"] = False

LABELS = {"Napa_cabbage_fall": "배추(가을)", "Dried_chili": "건고추"}

# --- 데이터 로드 ---
enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

# --- 가격을 wide 포맷으로 (날짜 x 품목) ---
wide = prices.pivot_table(index="date", columns="name", values="price")
merged = enso.merge(wide, on="date", how="inner").sort_values("date")
merged.to_csv(config.PROCESSED_DIR / "merged_analysis.csv", index=False, encoding="utf-8-sig")
print("결합 완료:", merged.shape[0], "개월")
print("기간:", merged.date.min().date(), "~", merged.date.max().date())

# --- 시각화: 품목별로 ENSO 시기 배경 칠하기 ---
items = [c for c in wide.columns]
fig, axes = plt.subplots(len(items), 1, figsize=(13, 4 * len(items)), sharex=True)
if len(items) == 1:
    axes = [axes]

for ax, item in zip(axes, items):
    sub = merged.dropna(subset=[item])
    ax.plot(sub["date"], sub[item], color="black", lw=1.2, label=LABELS.get(item, item))
    # 엘니뇨=빨강, 라니냐=파랑 배경
    for _, r in merged.iterrows():
        if r["phase"] == "El Nino":
            ax.axvspan(r["date"], r["date"] + pd.offsets.MonthBegin(1), color="red", alpha=0.12)
        elif r["phase"] == "La Nina":
            ax.axvspan(r["date"], r["date"] + pd.offsets.MonthBegin(1), color="blue", alpha=0.12)
    ax.set_title(f"{LABELS.get(item, item)} 도매가격  (빨강=엘니뇨, 파랑=라니냐)")
    ax.set_ylabel("원")
    ax.grid(alpha=0.3)

plt.tight_layout()
out = config.PROCESSED_DIR / "price_enso_plot.png"
plt.savefig(out, dpi=130)
print("그래프 저장:", out)
