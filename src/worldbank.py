"""
src/worldbank.py — World Bank "Pink Sheet" 월별 원자재 가격

용도:
  - 글로벌 농산물 선도/현물 가격 (밀, 옥수수, 대두, 설탕 등)
  - 교란변수: 원유(유가), 비료(요소·DAP 등)
"Monthly Prices" 시트의 날짜는 '1960M01' 형식 → datetime 으로 변환.
"""
import pandas as pd

import config
from src.utils import download_file


def fetch_pinksheet(force: bool = False) -> pd.DataFrame:
    """Pink Sheet 월별 가격을 long 포맷 직전의 wide 데이터프레임으로 반환.

    반환: date(인덱스 아님, 컬럼) + 각 원자재 컬럼.
    엑셀 구조가 바뀌면 skiprows / sheet_name 을 조정하세요.
    """
    try:
        path = download_file(
            config.WORLDBANK_PINKSHEET_URL,
            config.RAW_DIR / "wb_pinksheet_monthly.xlsx",
            force,
        )
    except RuntimeError:
        print("  [warn] 기본 URL 실패 → fallback URL 시도")
        path = download_file(
            config.WORLDBANK_PINKSHEET_FALLBACK,
            config.RAW_DIR / "wb_pinksheet_monthly.xlsx",
            force,
        )

    # "Monthly Prices" 시트: 상단에 설명/단위 행이 있어 헤더가 4~6행쯤에 위치.
    # 실제 파일을 한 번 열어보고 skiprows 를 맞추는 게 안전합니다.
    raw = pd.read_excel(path, sheet_name="Monthly Prices", skiprows=4)

    # 첫 컬럼이 '1960M01' 같은 날짜. 컬럼명이 깨질 수 있어 위치로 접근.
    raw = raw.rename(columns={raw.columns[0]: "period"})
    raw = raw.dropna(subset=["period"])
    raw["date"] = pd.to_datetime(
        raw["period"].astype(str).str.replace("M", "-", regex=False),
        format="%Y-%m",
        errors="coerce",
    )
    raw = raw.dropna(subset=["date"])

    # 기간 필터
    mask = (raw["date"] >= config.START_DATE) & (raw["date"] <= config.END_DATE)
    raw = raw.loc[mask]

    cols = ["date"] + [c for c in raw.columns if c not in ("period", "date")]
    return raw[cols].reset_index(drop=True)


# 관심 컬럼만 골라내는 헬퍼 (컬럼명은 실제 파일 확인 후 조정).
CONTROL_HINTS = {
    "crude_oil": "Crude oil, average",
    "urea": "Urea",
    "dap": "DAP",
    "wheat": "Wheat, US HRW",
    "maize": "Maize",
    "soybean": "Soybeans",
    "sugar": "Sugar, world",
}


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """이름 힌트로 필요한 컬럼만 추출(부분일치). 못 찾으면 건너뜀."""
    keep = {"date": "date"}
    for alias, hint in CONTROL_HINTS.items():
        for c in df.columns:
            if isinstance(c, str) and hint.lower() in c.lower():
                keep[c] = alias
                break
    out = df[list(keep)].rename(columns=keep)
    return out
