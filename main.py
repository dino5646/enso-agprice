"""main.py — 데이터 수집 파이프라인"""
import src.noaa as noaa
import src.worldbank as worldbank
import src.kamis as kamis
import src.fx as fx
from src.utils import save_processed


def run():
    print("\n[1/4] NOAA ENSO 지수 (ONI/RONI)")
    enso = noaa.fetch_enso()
    save_processed(enso, "enso_indices.csv")

    print("\n[2/4] World Bank Pink Sheet")
    try:
        wb = worldbank.fetch_pinksheet()
        wb = worldbank.select_columns(wb)
        save_processed(wb, "worldbank_commodities.csv")
    except Exception as e:
        print(f"  [skip] {e}")

    print("\n[3/4] USD/KRW 환율 (FRED)")
    try:
        fxdf = fx.fetch_fx()
        save_processed(fxdf, "usdkrw.csv")
        print(fxdf.tail(2).to_string(index=False))
    except Exception as e:
        print(f"  [skip] {e}")

    print("\n[4/4] KAMIS 농수산물 가격")
    try:
        prices = kamis.fetch_prices()
        save_processed(prices, "kamis_prices.csv")
    except RuntimeError as e:
        print(f"  [skip] {e}")

    print("\n완료. data/processed/ 를 확인하세요.")


if __name__ == "__main__":
    run()
