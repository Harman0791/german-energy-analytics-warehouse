-- Hourly prices with the previous hour's price, for change analysis.

SELECT
    timestamp_utc,
    date,
    hour_of_day,
    france,
    germany,
    belgium,
    spain,
    LAG(france)  OVER (ORDER BY timestamp_utc) AS france_prev,
    LAG(germany) OVER (ORDER BY timestamp_utc) AS germany_prev
FROM {{ ref('int_prices_hourly_wide') }}