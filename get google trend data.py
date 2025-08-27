# If running in Colab / Jupyter and pytrends isn't installed, uncomment:
# !pip install --quiet pytrends tqdm

from pytrends.request import TrendReq
import pandas as pd
from time import sleep
from datetime import datetime
from typing import List, Optional

# ---------------------------
# Config
# ---------------------------
KW_LIST = ["Squid Game"]          # keywords to track
TIMEFRAME = "2025-01-01 2025-08-01"  # date range (YYYY-MM-DD YYYY-MM-DD)
# Asia/Jakarta is UTC+7 => tz=420. (Your original code used 360 = UTC+6)
TZ_OFFSET_MINUTES = 420

# Top countries (ISO-2 codes). You can trim/extend this list.
COUNTRIES = [
    "US","KR","GB","IN","ID","BR","FR","DE","JP","MX",
    "CA","IT","ES","AU","RU","TR","NL","AR","SA","SE",
    "ZA","NG","PH","PL","EG","TH","VN","BD","PK","CO",
    "CL","PE","MY","SG","HK","AE","IL","IR","IQ","UA",
    "BE","CH","AT","DK","FI","NO","CZ","GR","HU","PT",
    "RO","NZ","IE","SK","BG","HR","RS","SI","LT","LV",
    "EE","LU","KE","GH","MA","DZ","TN","ET","TZ","UG",
    "KZ","UZ","AZ","QA","KW","OM","BH","JO","LB","YE"
]

# Output filenames (timestamped for reproducibility)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
FN_WORLD_IOT = f"trends_worldwide_iot_{STAMP}.csv"
FN_IBR_COUNTRY = f"trends_interest_by_country_{STAMP}.csv"
FN_IOT_BY_COUNTRY = f"trends_iot_by_country_{STAMP}.csv"

# Rate limiting / retries
SLEEP_SECONDS = 1.0          # polite delay between requests
MAX_RETRIES = 3              # per-country retries on failure
RETRY_BACKOFF = 2.0          # exponential backoff multiplier


# ---------------------------
# Helpers
# ---------------------------
def _drop_is_partial(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the 'isPartial' column if present."""
    if isinstance(df, pd.DataFrame) and "isPartial" in df.columns:
        return df.drop(columns=["isPartial"])
    return df


def _build(py: TrendReq, keywords: List[str], timeframe: str, geo: str = "") -> None:
    """Wrapper around build_payload with consistent arguments."""
    py.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)


def fetch_interest_over_time(py: TrendReq, keywords: List[str], timeframe: str, geo: str = "") -> pd.DataFrame:
    """Fetch interest over time for a given geo ('' = worldwide)."""
    _build(py, keywords, timeframe, geo)
    df = py.interest_over_time()
    if df is None or df.empty:
        return pd.DataFrame()
    df = _drop_is_partial(df)
    # If multi-keyword, keep all; otherwise ensure a predictable single-column name
    return df.reset_index()


def fetch_interest_by_region(py: TrendReq, keywords: List[str], timeframe: str, resolution: str = "COUNTRY") -> pd.DataFrame:
    """Fetch interest by region (e.g., COUNTRY) for provided timeframe."""
    _build(py, keywords, timeframe, geo="")
    df = py.interest_by_region(resolution=resolution, inc_low_vol=True, inc_geo_code=True)
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def fetch_iot_for_countries(py: TrendReq, keywords: List[str], timeframe: str, countries: List[str]) -> pd.DataFrame:
    """Fetch interest-over-time series for each country in list, with retries and rate limiting."""
    rows = []
    for c in countries:
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                df = fetch_interest_over_time(py, keywords, timeframe, geo=c)
                if not df.empty:
                    # Insert geo and tidy columns
                    df.insert(0, "geo", c)
                    rows.append(df)
                break  # success
            except Exception as e:
                attempt += 1
                if attempt >= MAX_RETRIES:
                    # Record a minimal row with error info (optional)
                    # print(f"[WARN] Failed for {c} after {MAX_RETRIES} retries: {e}")
                    pass
                else:
                    sleep(SLEEP_SECONDS * (RETRY_BACKOFF ** (attempt - 1)))
        sleep(SLEEP_SECONDS)  # polite delay after each country
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ---------------------------
# Main execution
# ---------------------------
def main(
    kw_list: Optional[List[str]] = None,
    timeframe: str = TIMEFRAME,
    countries: Optional[List[str]] = None,
    tz_offset_minutes: int = TZ_OFFSET_MINUTES
):
    kw_list = kw_list or KW_LIST
    countries = countries or COUNTRIES

    # Initialize pytrends
    pytrends = TrendReq(hl="en-US", tz=tz_offset_minutes)

    # 1) Worldwide Interest Over Time
    iot_world = fetch_interest_over_time(pytrends, kw_list, timeframe, geo="")
    if not iot_world.empty:
        iot_world.to_csv(FN_WORLD_IOT, index=False)

    # 2) Interest by Region (COUNTRY)
    ibr_country = fetch_interest_by_region(pytrends, kw_list, timeframe, resolution="COUNTRY")
    if not ibr_country.empty:
        # Sort by first keyword descending
        sort_col = kw_list[0] if kw_list[0] in ibr_country.columns else ibr_country.columns[0]
        ibr_country = ibr_country.sort_values(sort_col, ascending=False)
        ibr_country.to_csv(FN_IBR_COUNTRY, index=True)  # index includes region name

    # 3) Interest Over Time by Country list
    iot_by_country = fetch_iot_for_countries(pytrends, kw_list, timeframe, countries)
    if not iot_by_country.empty:
        # Ensure consistent column order: geo, date, keywords...
        cols = ["geo", "date"] + [c for c in iot_by_country.columns if c not in ("geo", "date")]
        iot_by_country = iot_by_country[cols]
        iot_by_country.to_csv(FN_IOT_BY_COUNTRY, index=False)

    # Optional: return dataframes for interactive sessions
    return {
        "world_iot": iot_world,
        "ibr_country": ibr_country,
        "iot_by_country": iot_by_country,
        "files": {
            "world_iot": FN_WORLD_IOT if not iot_world.empty else None,
            "ibr_country": FN_IBR_COUNTRY if not ibr_country.empty else None,
            "iot_by_country": FN_IOT_BY_COUNTRY if not iot_by_country.empty else None,
        },
    }


# If running as a script/notebook cell:
if __name__ == "__main__":
    out = main()
    # Quick peek (safe even if empty)
    for name, df in [("world_iot", out["world_iot"]), ("ibr_country", out["ibr_country"]), ("iot_by_country", out["iot_by_country"])]:
        print(f"\n>>> {name} preview:")
        try:
            print(df.tail())
        except Exception:
            print("(no data)")
    print("\nSaved files:", out["files"])