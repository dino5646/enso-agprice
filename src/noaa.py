"""
src/noaa.py — NOAA CPC 의 ONI / RONI ENSO 지수 수집

두 파일 모두 공백 구분 텍스트:
  ONI : SEAS YR TOTAL ANOM   (ANOM 이 지수값)
  RONI: SEAS YR ANOM

SEAS 는 3개월 계절 코드(DJF, JFM, ...). 각 계절의 '중앙월'로 월별 날짜를 만든다:
  DJF→1월, JFM→2월, ..., NDJ→12월
"""
import pandas as pd

import config
from src.utils import download_file

# 계절 코드 → 중앙월(1~12)
SEASON_TO_MONTH = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def _parse(path, value_col: str, out_name: str) -> pd.DataFrame:
    """공백 구분 파일을 (date, <out_name>) 데이터프레임으로 변환."""
    df = pd.read_csv(path, sep=r"\s+")
    df["month"] = df["SEAS"].map(SEASON_TO_MONTH)
    df["date"] = pd.to_datetime(
        df["YR"].astype(str) + "-" + df["month"].astype(str) + "-01"
    )
    df = df[["date", value_col]].rename(columns={value_col: out_name})
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_oni(force: bool = False) -> pd.DataFrame:
    """ONI 지수. 반환: date, oni"""
    path = download_file(config.NOAA_ONI_URL, config.RAW_DIR / "oni.ascii.txt", force)
    return _parse(path, value_col="ANOM", out_name="oni")


def fetch_roni(force: bool = False) -> pd.DataFrame:
    """RONI 지수(2026-02 이후 공식 지표). 반환: date, roni"""
    path = download_file(config.NOAA_RONI_URL, config.RAW_DIR / "roni.ascii.txt", force)
    return _parse(path, value_col="ANOM", out_name="roni")


def fetch_enso(force: bool = False) -> pd.DataFrame:
    """ONI + RONI 를 date 기준으로 병합. 반환: date, oni, roni"""
    oni = fetch_oni(force)
    roni = fetch_roni(force)
    merged = pd.merge(oni, roni, on="date", how="outer").sort_values("date")
    # ENSO 국면 라벨 (ONI 기준: ±0.5 임계)
    def phase(x):
        if pd.isna(x):
            return None
        if x >= 0.5:
            return "El Nino"
        if x <= -0.5:
            return "La Nina"
        return "Neutral"
    merged["phase"] = merged["oni"].map(phase)
    return merged.reset_index(drop=True)
