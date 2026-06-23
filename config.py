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

# items to analyze (category 200 = vegetables)
KAMIS_ITEMS = [
    {"name": "Napa_cabbage_fall", "category": "200", "item": "211", "kind": "03"},
    {"name": "Dried_chili", "category": "200", "item": "241", "kind": "00"},
]

KAMIS_PRODUCT_CLS = "02"   # 01 retail, 02 wholesale
KAMIS_GRADE_RANK = "2"     # 1 top, 2 mid

HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
