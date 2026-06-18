"""
src/kamis.py — KAMIS Open API 로 한국 농수산물 도·소매가격 수집

이 모듈을 쓰려면 .env 에 KAMIS_CERT_KEY, KAMIS_CERT_ID 가 있어야 합니다.
사용 액션: periodProductList (일별 품목별 도·소매가격, 기간 지정)
"""
import pandas as pd

import config
from src.utils import get_json


def _fetch_one_item(item: dict, start: str, end: str) -> pd.DataFrame:
    """단일 품목의 기간별 가격을 받아온다."""
    params = {
        "action": "periodProductList",
        "p_productclscode": config.KAMIS_PRODUCT_CLS,   # 01 소매 / 02 도매
        "p_startday": start,
        "p_endday": end,
        "p_itemcategorycode": item["category"],
        "p_itemcode": item["item"],
        "p_kindcode": item["kind"],
        "p_productrankcode": config.KAMIS_PRODUCT_RANK,
        "p_convert_kg_yn": "N",
        "p_cert_key": config.KAMIS_CERT_KEY,
        "p_cert_id": config.KAMIS_CERT_ID,
        "p_returntype": "json",
    }
    data = get_json(config.KAMIS_BASE_URL, params)

    # 응답 구조가 버전에 따라 다를 수 있어 방어적으로 파싱.
    rows = []
    payload = data.get("data", data)
    items = payload.get("item", []) if isinstance(payload, dict) else payload
    if isinstance(items, dict):
        items = [items]
    for row in items or []:
        # 대표 필드: regday(날짜), price(가격). 키 이름은 명세서 기준 조정.
        rows.append(
            {
                "name": item["name"],
                "regday": row.get("regday") or row.get("yyyy"),
                "price": row.get("price"),
            }
        )
    df = pd.DataFrame(rows)
    return df


def fetch_prices(start: str = None, end: str = None) -> pd.DataFrame:
    """config.KAMIS_ITEMS 의 모든 품목 가격을 수집해 합친다.

    반환: name, date, price
    """
    if not config.KAMIS_CERT_KEY or not config.KAMIS_CERT_ID:
        raise RuntimeError(
            "KAMIS 인증 정보가 없습니다. .env 에 KAMIS_CERT_KEY / KAMIS_CERT_ID 를 넣으세요."
        )
    if not config.KAMIS_ITEMS:
        raise RuntimeError(
            "config.KAMIS_ITEMS 가 비어 있습니다. 분석할 품목 코드를 채워주세요."
        )

    start = start or config.START_DATE
    end = end or config.END_DATE

    frames = []
    for item in config.KAMIS_ITEMS:
        print(f"  [kamis] {item['name']} 수집 중...")
        df = _fetch_one_item(item, start, end)
        frames.append(df)

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        # 가격 문자열에서 콤마 제거 후 숫자화, 날짜 파싱
        out["price"] = (
            out["price"].astype(str).str.replace(",", "", regex=False)
        )
        out["price"] = pd.to_numeric(out["price"], errors="coerce")
        out["date"] = pd.to_datetime(out["regday"], errors="coerce")
        out = out.dropna(subset=["date", "price"])[["name", "date", "price"]]
    return out.reset_index(drop=True)
