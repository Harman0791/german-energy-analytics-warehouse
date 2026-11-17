-- 24-hour rolling average price per country.

SELECT
    timestamp_utc,
    date,
    hour_of_day,
    AVG(france)  OVER w AS france_ra_24h,
    AVG(germany) OVER w AS germany_ra_24h,
    AVG(belgium) OVER w AS belgium_ra_24h,
    AVG(spain)   OVER w AS spain_ra_24h
FROM {{ ref('int_prices_hourly_wide') }}
WINDOW w AS (ORDER BY timestamp_utc ROWS BETWEEN 23 PRECEDING AND CURRENT ROW)