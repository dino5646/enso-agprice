"""
config.py — 프로젝트 전역 설정
ENSO(엘니뇨/라니냐) ↔ 농수산물 가격 상관관계 연구

API 키 같은 민감 정보는 코드에 직접 쓰지 말고 .env 파일에 두세요.
(.env 는 .gitignore 에 포함 → GitHub 에 올라가지 않음)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # 같은 폴더의 .env 를 환경변수로 로드

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 연구 기간 (필요에 맞게 조정)
# ---------------------------------------------------------------------------
START_DATE = "2010-01-01"
END_DATE = "2025-12-31"

# ---------------------------------------------------------------------------
# NOAA ENSO 지수 (공백 구분 텍스트, 인증 불필요)
# ---------------------------------------------------------------------------
# ONI 컬럼: SEAS YR TOTAL ANOM   /   RONI 컬럼: SEAS YR ANOM
# RONI 는 2026-02 부터 NOAA 공식 ENSO 모니터링 지표. 둘 다 받아 강건성 비교 권장.
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
NOAA_RONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt"

# ---------------------------------------------------------------------------
# World Bank "Pink Sheet" — 월별 원자재 가격 (유가/비료 통제변수 포함)
# ---------------------------------------------------------------------------
# 주의: 이 URL 의 해시값은 World Bank 가 주기적으로 갱신합니다.
# 404 가 뜨면 worldbank.org/en/research/commodity-markets 에서 최신
# "Monthly prices" 엑셀 링크를 복사해 아래 값을 교체하세요.
WORLDBANK_PINKSHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "18675f1d1639c7a34d463f59263ba0a2-0050012025/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
# 레거시 안정 URL (위가 막히면 시도): 
WORLDBANK_PINKSHEET_FALLBACK = (
    "http://pubdocs.worldbank.org/en/561011486076393416/"
    "CMO-Historical-Data-Monthly.xlsx"
)

# ---------------------------------------------------------------------------
# KAMIS Open API — 한국 농수산물 도·소매가격 (인증 필요)
# ---------------------------------------------------------------------------
# 1) kamis.or.kr 회원가입 → 고객센터 > Open-API > 이용신청 으로 키 발급
# 2) 발급받은 값을 .env 에 KAMIS_CERT_KEY / KAMIS_CERT_ID 로 저장
KAMIS_BASE_URL = "https://www.kamis.or.kr/service/price/xml.do"
KAMIS_CERT_KEY = os.getenv("KAMIS_CERT_KEY", "")
KAMIS_CERT_ID = os.getenv("KAMIS_CERT_ID", "")

# 분석할 품목 목록.
# 부류코드: 100 식량작물 200 채소류 300 특용작물 400 과일류 500 축산물 600 수산물
# item_code / kind_code 는 KAMIS Open-API 명세의 코드표를 보고 채우세요.
# (아래는 예시 — 실제 코드는 발급 후 명세서에서 확인)
KAMIS_ITEMS = [
    {"name": "배추(가을)", "category": "200", "item": "211", "kind": "03"},
    {"name": "건고추(화건)", "category": "200", "item": "241", "kind": "00"},
    {"name": "깐마늘(국산)", "category": "200", "item": "258", "kind": "01"},
]

# 도·소매 구분: 01 소매, 02 도매
KAMIS_PRODUCT_CLS = "02"
# 등급코드: 04 상품, 05 중품
KAMIS_PRODUCT_RANK = "04"

# 네트워크 재시도
HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
