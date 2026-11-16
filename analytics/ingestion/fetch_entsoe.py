import os
import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

load_dotenv()


def fetch_prices(client, zone, start, end):
    """Day-ahead prices for one bidding zone as hourly rows in UTC."""
    prices = client.query_day_ahead_prices(zone, start=start, end=end)

    # 1. Keep [start, end): the API also returns the end timestamp
    prices = prices[prices.index < end]

    # 2. Convert to UTC: no DST gaps or duplicate hours
    prices.index = prices.index.tz_convert("UTC")

    # 3. 15-minute prices (since Oct 2025) -> hourly average
    prices = prices.resample("1h").mean()

    df = prices.to_frame("price_eur_mwh")
    df.index.name = "timestamp_utc"
    df = df.reset_index()
    df["bidding_zone"] = zone
    return df


if __name__ == "__main__":
    client = EntsoePandasClient(api_key=os.getenv("ENTSOE_API_KEY"))

    # Test 1: switch from hourly to 15-minute prices (1 Oct 2025)
    df = fetch_prices(client, "DE_LU",
                      pd.Timestamp("2025-09-29", tz="Europe/Berlin"),
                      pd.Timestamp("2025-10-03", tz="Europe/Berlin"))
    print("Test 1 rows:", len(df), "(expected 96)")

    # Test 2: autumn DST change (26 Oct 2025 has 25 hours)
    df = fetch_prices(client, "DE_LU",
                      pd.Timestamp("2025-10-25", tz="Europe/Berlin"),
                      pd.Timestamp("2025-10-27", tz="Europe/Berlin"))
    print("Test 2 rows:", len(df), "(expected 49)")
    print(df.head())