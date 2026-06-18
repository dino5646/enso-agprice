"""
src/utils.py — 공용 헬퍼
"""
import time
from pathlib import Path

import requests

import config


def download_file(url: str, dest: Path, force: bool = False) -> Path:
    """url 을 dest 로 다운로드. 이미 있으면 캐시 사용(force=True 면 재다운로드)."""
    if dest.exists() and not force:
        print(f"  [cache] {dest.name} 이미 존재 → 재사용")
        return dest

    last_err = None
    for attempt in range(1, config.HTTP_RETRIES + 1):
        try:
            print(f"  [get ] {url}  (시도 {attempt})")
            r = requests.get(url, timeout=config.HTTP_TIMEOUT)
            r.raise_for_status()
            dest.write_bytes(r.content)
            print(f"  [save] {dest}  ({len(r.content):,} bytes)")
            return dest
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"다운로드 실패: {url}\n{last_err}")


def get_json(url: str, params: dict) -> dict:
    """JSON API 호출 (KAMIS 용). 재시도 포함."""
    last_err = None
    for attempt in range(1, config.HTTP_RETRIES + 1):
        try:
            r = requests.get(url, params=params, timeout=config.HTTP_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"API 호출 실패: {url}\n{last_err}")


def save_processed(df, name: str):
    """전처리 결과를 data/processed 에 CSV 로 저장."""
    out = config.PROCESSED_DIR / name
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"  [out ] {out}  ({len(df):,} rows)")
    return out
