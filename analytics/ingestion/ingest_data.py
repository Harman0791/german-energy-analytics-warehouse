import os
import pandas as pd
import sqlalchemy as sa
from dotenv import load_dotenv
from entsoe import EntsoePandasClient
from fetch_entsoe import fetch_prices

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


def ingest():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(sa.text(CREATE_TABLE))

    client = EntsoePandasClient(
        api_key=os.getenv("ENTSOE_API_KEY"),
        timeout=60,        # give up on a request after 60 seconds
        retry_count=3,     # then try again, up to 3 times
        retry_delay=10,    # wait 10 seconds between tries
    )
    end = pd.Timestamp.now(tz="Europe/Berlin").normalize()  # today 00:00 -> data until yesterday

    for zone in ZONES:
        chunk_start = START
        while chunk_start < end:
            # Load one month at a time
            chunk_end = min(chunk_start + pd.DateOffset(months=1), end)
            print(f"{zone}: {chunk_start.date()} to {chunk_end.date()} ...", flush=True)

            df = fetch_prices(client, zone, chunk_start, chunk_end)
            load_zone(engine, df, zone, chunk_start, chunk_end)

            print(f"   {len(df)} rows loaded", flush=True)
            chunk_start = chunk_end


if __name__ == "__main__":
    ingest()