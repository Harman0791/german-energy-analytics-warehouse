import os
import pandas as pd
import sqlalchemy as sa
import argparse
import time
from dotenv import load_dotenv
from entsoe import EntsoePandasClient
from fetch_entsoe import fetch_prices
from requests.exceptions import HTTPError, ConnectionError, Timeout


load_dotenv()

ZONES = ["DE_LU", "FR", "ES", "BE"]
START = pd.Timestamp("2023-01-01", tz="Europe/Berlin")

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS raw_dayahead_prices (
    timestamp_utc  TIMESTAMPTZ NOT NULL,
    bidding_zone   TEXT        NOT NULL,
    price_eur_mwh  NUMERIC,
    loaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (timestamp_utc, bidding_zone)
);
"""


DELETE_RANGE = """
DELETE FROM raw_dayahead_prices
WHERE bidding_zone = :zone
  AND timestamp_utc >= :start
  AND timestamp_utc <  :end;
"""

def get_engine():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    return sa.create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")


def load_zone(engine, df, zone, start, end):
    # One transaction: delete the range, then insert it fresh
    with engine.begin() as conn:
        conn.execute(sa.text(DELETE_RANGE), {"zone": zone, "start": start, "end": end})
        df.to_sql("raw_dayahead_prices", conn, if_exists="append", index=False)

def fetch_with_retry(client, zone, start, end, attempts=5):
    """Retry failed API calls, waiting longer after each failure (backoff)."""
    for attempt in range(1, attempts + 1):
        try:
            return fetch_prices(client, zone, start, end)
        except (HTTPError, ConnectionError, Timeout) as error:
            if attempt == attempts:
                raise
            wait = 30 * attempt
            # Print only the error type: the full message contains the API key
            print(f"   attempt {attempt} failed ({type(error).__name__}), "
                  f"retrying in {wait}s ...", flush=True)
            time.sleep(wait)

def ingest(full=False):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(sa.text(CREATE_TABLE))
    # First run on an empty database: load the full history automatically
    with engine.connect() as conn:
        row_count = conn.execute(sa.text("SELECT COUNT(*) FROM raw_dayahead_prices")).scalar()
    if row_count == 0:
        full = True

    client = EntsoePandasClient(
        api_key=os.getenv("ENTSOE_API_KEY"),
        timeout=60,        # give up on a request after 60 seconds
        retry_count=3,     # then try again, up to 3 times
        retry_delay=10,    # wait 10 seconds between tries
    )  

    end = pd.Timestamp.now(tz="Europe/Berlin").normalize()  # today 00:00 -> data until yesterday
    start = START if full else end - pd.DateOffset(days=7)
    print(f"Mode: {'full' if full else 'incremental'}, loading from {start.date()}", flush=True)

    for zone in ZONES:
        chunk_start = start
        while chunk_start < end:
            # Load one month at a time
            chunk_end = min(chunk_start + pd.DateOffset(months=1), end)
            print(f"{zone}: {chunk_start.date()} to {chunk_end.date()} ...", flush=True)

            df = fetch_with_retry(client, zone, chunk_start, chunk_end)
            load_zone(engine, df, zone, chunk_start, chunk_end)

            print(f"   {len(df)} rows loaded", flush=True)
            chunk_start = chunk_end


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load ENTSO-E day-ahead prices")
    parser.add_argument("--full", action="store_true",
                        help="reload all data since 2023 instead of the last 7 days")
    args = parser.parse_args()
    ingest(full=args.full)