"""
main.py — 데이터 수집 파이프라인 진입점

실행:  python main.py
- NOAA ENSO(ONI/RONI)  : 키 불필요, 항상 수집
- World Bank Pink Sheet : 키 불필요, 항상 수집
- KAMIS 농수산물 가격   : 키가 있을 때만 수집
결과는 data/processed/ 에 CSV 로 저장됩니다.
"""
import src.noaa as noaa
import src.worldbank as worldbank
import src.kamis as kamis
from src.utils import save_processed


def run():
    print("\n[1/3] NOAA ENSO 지수 (ONI/RONI)")
    enso = noaa.fetch_enso()
    save_processed(enso, "enso_indices.csv")
    print(enso.tail(3).to_string(index=False))

    print("\n[2/3] World Bank Pink Sheet (원자재·유가·비료)")
    try:
        wb = worldbank.fetch_pinksheet()
        wb = worldbank.select_columns(wb)
        save_processed(wb, "worldbank_commodities.csv")
        print(wb.tail(3).to_string(index=False))
    except Exception as e:  # 엑셀 구조 변동 등은 치명적이지 않게 처리
        print(f"  [skip] World Bank 수집 실패: {e}")

    print("\n[3/3] KAMIS 농수산물 가격")
    try:
        prices = kamis.fetch_prices()
        save_processed(prices, "kamis_prices.csv")
        print(prices.tail(3).to_string(index=False))
    except RuntimeError as e:
        print(f"  [skip] {e}")

    print("\n완료. data/processed/ 를 확인하세요.")


if __name__ == "__main__":
    run()
