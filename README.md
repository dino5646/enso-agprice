# ENSO × Agricultural Price Study

Data pipeline for analyzing the relationship between **ENSO (El Niño / La Niña)**
and **agricultural & fisheries prices**. Built as an undergraduate thesis project
(Earth Science Education × Industrial Engineering, Seoul National University).

> 엘니뇨·라니냐(ENSO)와 농수산물 가격의 상관관계를 분석하기 위한 데이터 수집
> 파이프라인입니다. 세 개의 공개 데이터 소스를 자동으로 받아와 정리합니다.

## Data sources

| Source | What | Auth | Frequency |
|---|---|---|---|
| NOAA CPC ONI / RONI | ENSO index (independent variable) | none | monthly |
| World Bank Pink Sheet | global commodities, crude oil, fertilizer (controls) | none | monthly |
| KAMIS Open API (aT) | Korean wholesale/retail produce prices (dependent variable) | API key | daily |

Note: NOAA replaced ONI with **RONI** as the official ENSO index in Feb 2026.
This pipeline pulls both so results can be checked for robustness.

## Project structure

```
enso-agprice/
├── config.py            # URLs, date range, item codes, API keys (via .env)
├── main.py              # run the full pipeline
├── requirements.txt
├── .env.example         # copy to .env and fill in KAMIS credentials
├── src/
│   ├── noaa.py          # ONI/RONI fetch + season→month parsing
│   ├── worldbank.py     # Pink Sheet xlsx fetch + column selection
│   ├── kamis.py         # KAMIS Open API client
│   └── utils.py         # download/caching/save helpers
└── data/
    ├── raw/             # cached downloads (gitignored)
    └── processed/       # merged CSV output
```

## Setup

```bash
git clone <your-repo-url>
cd enso-agprice
python -m venv .venv && source .venv/bin/activate   # optional
pip install -r requirements.txt

cp .env.example .env        # then add your KAMIS key/id
python main.py
```

NOAA and World Bank run without any credentials. KAMIS is skipped automatically
until you register at [kamis.or.kr](https://www.kamis.or.kr) → 고객센터 > Open-API
and put `KAMIS_CERT_KEY` / `KAMIS_CERT_ID` in `.env`.

## Output

`data/processed/`:
- `enso_indices.csv` — `date, oni, roni, phase`
- `worldbank_commodities.csv` — `date, crude_oil, urea, dap, wheat, maize, soybean, sugar`
- `kamis_prices.csv` — `name, date, price`

## Methodology notes (next steps)

The collection layer is deliberate about confounders. Agricultural prices are driven
by more than ENSO, so the analysis controls for:

- **Real prices** — deflate nominal prices (CPI / World Bank MUV) before modeling.
- **Seasonality & trend** — deseasonalize (X-13ARIMA-SEATS); test stationarity
  (ADF, KPSS) to avoid spurious regression.
- **Lag structure** — ENSO → weather → crop → price has a multi-month lag tied to
  planting/harvest cycles; use distributed-lag / ARDL.
- **Controls** — crude oil, fertilizer, FX, other teleconnections (IOD, NAO).
- **ENSO is exogenous** — human economic activity does not cause El Niño, so reverse
  causality is minimal. This makes ENSO usable as an exogenous shock / instrument.

## License

MIT (or your choice).
