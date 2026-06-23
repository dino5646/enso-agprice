"""
src/kamis.py — KAMIS 월별 도·소매가격 수집 (monthlySalesList)
연도별 m1~m12 구조를 (name, date, price) 행으로 펼침.
"""
import ssl
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

import config


class _KamisTLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


_SESSION = requests.Session()
_SESSION.mount("https://", _KamisTLSAdapter())


def get_json(url, params):
    last_err = None
    for _ in range(config.HTTP_RETRIES):
        try:
            r = _SESSION.get(url, params=params, timeout=config.HTTP_TIMEOUT, verify=False)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(f"API 호출 실패: {url}\n{last_err}")


def _parse_monthly(data, name, want_cls):
    """price[].item[] 의 연도별 m1~m12 를 (name, date, price) 로 펼침."""
    rows = []
    blocks = data.get("price", [])
    if isinstance(blocks, dict):
        blocks = [blocks]
    for block in blocks or []:
        if block.get("productclscode") != want_cls:
            continue
        items = block.get("item", [])
        if isinstance(items, dict):
            items = [items]
        for it in items:
            yyyy = it.get("yyyy")
            if not yyyy or not str(yyyy).isdigit():
                continue
            for mm in range(1, 13):
                val = it.get(f"m{mm}")
                if val in (None, "-", ""):
                    continue
                rows.append({
                    "name": name,
                    "date": f"{yyyy}-{mm:02d}-01",
                    "price": val,
                })
    return rows


def _fetch_item(item, end_year, period):
    params = {
        "action": "monthlySalesList",
        "p_yyyy": str(end_year),
        "p_period": str(period),
        "p_itemcategorycode": item["category"],
        "p_itemcode": item["item"],
        "p_kindcode": item["kind"],
        "p_graderank": config.KAMIS_GRADE_RANK,
        "p_convert_kg_yn": "N",
        "p_cert_key": config.KAMIS_CERT_KEY,
        "p_cert_id": config.KAMIS_CERT_ID,
        "p_returntype": "json",
    }
    data = get_json(config.KAMIS_BASE_URL, params)
    return _parse_monthly(data, item["name"], config.KAMIS_PRODUCT_CLS)


def fetch_prices(start=None, end=None):
    if not config.KAMIS_CERT_KEY or not config.KAMIS_CERT_ID:
        raise RuntimeError("KAMIS 인증 정보가 없습니다. .env 를 확인하세요.")
    if not config.KAMIS_ITEMS:
        raise RuntimeError("config.KAMIS_ITEMS 가 비어 있습니다.")

    start = start or config.START_DATE
    end = end or config.END_DATE
    start_year = int(start[:4])
    end_year = int(end[:4])
    period = end_year - start_year + 1   # 한 번에 받을 연수

    all_rows = []
    for item in config.KAMIS_ITEMS:
        print(f"  [kamis] {item['name']} 수집 중...", end="", flush=True)
        rows = _fetch_item(item, end_year, period)
        all_rows.extend(rows)
        print(f" {len(rows)}건")

    out = pd.DataFrame(all_rows)
    if not out.empty:
        out["price"] = out["price"].astype(str).str.replace(",", "", regex=False)
        out["price"] = pd.to_numeric(out["price"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out.dropna(subset=["date", "price"])
        out = out[(out["date"] >= start) & (out["date"] <= end)]
        out = out.drop_duplicates(subset=["name", "date"]).sort_values(["name", "date"])
        out = out[["name", "date", "price"]]
    return out.reset_index(drop=True)
