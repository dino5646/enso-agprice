"""src/fx.py — FRED 에서 USD/KRW 월별 환율 (DEXKOUS)"""
import pandas as pd
import config
from src.utils import download_file


def fetch_fx(force: bool = False) -> pd.DataFrame:
    """USD/KRW 월별 평균 환율. 반환: date, usdkrw"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXKOUS"
    path = download_file(url, config.RAW_DIR / "usdkrw.csv", force)
    df = pd.read_csv(path)
    df.columns = ["date", "usdkrw"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["usdkrw"] = pd.to_numeric(df["usdkrw"], errors="coerce")
    df = df.dropna()
    # 일별 → 월별 평균, 날짜를 월초로
    df = df.set_index("date").resample("MS")["usdkrw"].mean().reset_index()
    return df
