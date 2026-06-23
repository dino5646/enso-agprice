"""config.py — 프로젝트 전역 설정"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = "2010-01-01"
END_DATE = "2025-12-31"

NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
NOAA_RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

WORLDBANK_PINKSHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "18675f1d1639c7a34d463f59263ba0a2-0050012025/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
WORLDBANK_PINKSHEET_FALLBACK = (
    "http://pubdocs.worldbank.org/en/561011486076393416/"
    "CMO-Historical-Data-Monthly.xlsx"
)

KAMIS_BASE_URL = "https://www.kamis.or.kr/service/price/xml.do"
KAMIS_CERT_KEY = os.getenv("KAMIS_CERT_KEY", "")
KAMIS_CERT_ID = os.getenv("KAMIS_CERT_ID", "")

# 200=vegetables, 600=seafood
KAMIS_ITEMS = [
    {"name": "cabbage_spring", "category": "200", "item": "211", "kind": "01"},
    {"name": "cabbage_summer", "category": "200", "item": "211", "kind": "02"},
    {"name": "cabbage_fall", "category": "200", "item": "211", "kind": "03"},
    {"name": "cabbage_winter", "category": "200", "item": "211", "kind": "06"},
    {"name": "Dried_chili", "category": "200", "item": "241", "kind": "00"},
    {"name": "mackerel", "category": "600", "item": "611", "kind": "01"},
    {"name": "squid", "category": "600", "item": "619", "kind": "01"},
    {"name": "hairtail", "category": "600", "item": "613", "kind": "01"},
]

KAMIS_PRODUCT_CLS = "02"
KAMIS_GRADE_RANK = "2"

HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
