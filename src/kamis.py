"""
src/kamis.py — KAMIS Open API 로 한국 농수산물 도·소매가격 수집
"""
import ssl
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

import config


class _KamisTLSAdapter(HTTPAdapter):
    """KAMIS 서버의 구형 SSL 설정에 맞춰 연결."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def get_json(url: str, params: dict) -> dict:
    """KAMIS 전용 SSL 어댑터로 JSON API 호출."""
    session = requests.Session()
    session.mount("https://", _KamisTLSAdapter())
    last_err = None
    for attempt in range(1, config.HTTP_RETRIES + 1):
        try:
            r = session.get(url, params=params, timeout=config.HTTP_TIMEOUT, verify=False)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
    raise RuntimeError(f"API 호출 실패: {url}\n{last_err}")


def _fetch_one_item(item: dict, start: str, end: str) -> pd.DataFrame:
    """단일 품목의 기간별 가격을 받아온다."""
    params = {
        "action": "periodProductList",
        "p_productclscode": config.KAMIS_PRODUCT_CLS,
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

    rows = []
    payload = data.get("data", {})
    items = payload.get("item", []) if isinstance(payload, dict) else []
    if isinstance(items, dict):
        items = [items]
    for row in items or []:
        if not isinstance(row, dict):
            continue
        yyyy = row.get("yyyy")
        regday = row.get("regday")
        price = row.get("price")
        if row.get("countyname") not in (None, "평균"):
            continue
        if not yyyy or not regday or price in (None, "-", ""):
            continue
        mm, dd = regday.split("/")
        date_str = f"{yyyy}-{mm}-{dd}"
        rows.append({"name": item["name"], "date": date_str, "price": price})
    return pd.DataFrame(rows)


def fetch_prices(start: str = None, end: str = None) -> pd.DataFrame:
    """config.KAMIS_ITEMS 의 모든 품목 가격을 수집해 합친다."""
    if not config.KAMIS_CERT_KEY or not config.KAMIS_CERT_ID:
        raise RuntimeError("KAMIS 인증 정보가 없습니다. .env 를 확인하세요.")
    if not config.KAMIS_ITEMS:
        raise RuntimeError("config.KAMIS_ITEMS 가 비어 있습니다.")

    start = start or config.START_DATE
    end = end or config.END_DATE

    frames = []
    for item in config.KAMIS_ITEMS:
        print("  [kamis] " + item["name"] + " 수집 중...")
        frames.append(_fetch_one_item(item, start, end))

    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not out.empty:
        out["price"] = out["price"].astype(str).str.replace(",", "", regex=False)
        out["price"] = pd.to_numeric(out["price"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out.dropna(subset=["date", "price"])[["name", "date", "price"]]
    return out.reset_index(drop=True)


