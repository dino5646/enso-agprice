"""catch.py — 어획량 변환 + RONI→어획량→가격 메커니즘 검증"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import openpyxl

import config

# --- 1) 어획량 엑셀 변환 (가로형 → 세로형) ---
wb = openpyxl.load_workbook(config.RAW_DIR / "catch.xlsx", data_only=True)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))

# 1행: 날짜 헤더(병합), 2행: 생산량:계 등 항목. 날짜는 4열부터 6칸 간격일 수 있음
date_row = rows[0]
item_row = rows[1]
# "생산량:계" 위치의 열 인덱스 + 그 위 날짜를 매핑
dates = {}
last_date = None
for j, v in enumerate(date_row):
    if v and isinstance(v, str) and "." in str(v):
        last_date = v
    if item_row[j] == "생산량:계":
        dates[j] = last_date

fish_map = {"갈치":"hairtail", "고등어":"mackerel", "살오징어(오징어)":"squid"}
records = []
for row in rows[2:]:
    name_raw = (row[1] or "").strip()
    for kor, eng in fish_map.items():
        if name_raw == kor:
            for j, d in dates.items():
                val = row[j]
                if isinstance(val,(int,float)):
                    # d 예: 2010.01 → 2010-01-01
                    d = d.split(" ")[0].strip(); y,m = d.split(".")[0], d.split(".")[1]; 
                    records.append({"name":eng, "date":f"{y}-{m}-01", "catch":val})

catch = pd.DataFrame(records)
catch["date"] = pd.to_datetime(catch["date"])
catch.to_csv(config.PROCESSED_DIR / "catch.csv", index=False, encoding="utf-8-sig")
print("어획량 변환 완료:", catch.shape[0], "행")
for n,g in catch.groupby("name"):
    print(f"  {n}: {g.date.min().date()} ~ {g.date.max().date()} ({len(g)}건)")

# --- 2) ENSO + 어획량 + 가격 결합 ---
enso = pd.read_csv(config.PROCESSED_DIR / "enso_indices.csv", parse_dates=["date"])
prices = pd.read_csv(config.PROCESSED_DIR / "kamis_prices.csv", parse_dates=["date"])

cw = catch.pivot_table(index="date", columns="name", values="catch").reset_index()
pw = prices[prices["name"].isin(["squid","hairtail","mackerel"])].pivot_table(index="date",columns="name",values="price").reset_index()
pw.columns = ["date"]+[f"price_{c}" for c in pw.columns[1:]]

df = enso[["date","oni","roni"]].merge(cw,on="date",how="inner").merge(pw,on="date",how="left").sort_values("date").reset_index(drop=True)
df["d_roni"]=df["roni"].diff(); df["d_oni"]=df["oni"].diff()
df["month"]=df["date"].dt.month
for f in ["squid","hairtail","mackerel"]:
    df[f"dlog_catch_{f}"]=np.log(df[f].replace(0,np.nan)).diff()
    if f"price_{f}" in df:
        df[f"dlog_price_{f}"]=np.log(df[f"price_{f}"]).diff()

print("\n"+"="*60)
print("  [검증 1] RONI → 어획량  (엘니뇨가 어획량을 바꾸나?)")
print("="*60)
for f,kor in [("squid","오징어"),("hairtail","갈치"),("mackerel","고등어")]:
    best=(None,1,None)
    for lag in range(0,7):
        d=df.copy(); d["x"]=d["d_roni"].shift(lag)
        sub=d.dropna(subset=[f"dlog_catch_{f}","x"])
        if len(sub)<20: continue
        m=smf.ols(f"dlog_catch_{f} ~ x + C(month)",data=sub).fit()
        if m.pvalues["x"]<best[1]: best=(lag,m.pvalues["x"],m.params["x"])
    s="**" if best[1]<0.05 else ("*" if best[1]<0.10 else "")
    print(f"  {kor}: {best[0]}월 시차, 계수 {best[2]:+.3f}, p={best[1]:.3f} {s}")

print("\n"+"="*60)
print("  [검증 2] 어획량 → 가격  (많이 잡히면 가격 내리나?)")
print("="*60)
for f,kor in [("squid","오징어"),("hairtail","갈치"),("mackerel","고등어")]:
    if f"dlog_price_{f}" not in df: continue
    sub=df.dropna(subset=[f"dlog_catch_{f}",f"dlog_price_{f}"])
    if len(sub)<20: 
        print(f"  {kor}: 데이터 부족"); continue
    m=smf.ols(f"dlog_price_{f} ~ dlog_catch_{f} + C(month)",data=sub).fit()
    c=m.params[f"dlog_catch_{f}"]; p=m.pvalues[f"dlog_catch_{f}"]
    s="**" if p<0.05 else ("*" if p<0.10 else "")
    print(f"  {kor}: 계수 {c:+.3f}, p={p:.3f} {s}  (음수면 '많이잡힘→가격하락' 확인)")

print("\n해석: 검증1에서 양수 + 검증2에서 음수 → 'RONI→어획량↑→가격↓' 사슬 성립")

