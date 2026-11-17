-- Absolute hour-to-hour price change per country.

SELECT
    timestamp_utc,
    date,
    hour_of_day,
    ABS(france  - LAG(france)  OVER w) AS france_volatility,
    ABS(germany - LAG(germany) OVER w) AS germany_volatility,
    ABS(belgium - LAG(belgium) OVER w) AS belgium_volatility,
    ABS(spain   - LAG(spain)   OVER w) AS spain_volatility
FROM {{ ref('int_prices_hourly_wide') }}
WINDOW w AS (ORDER BY timestamp_utc)