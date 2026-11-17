-- Daily average price per country (local calendar day).
-- Read by the forecasting and seasonality scripts.

SELECT
    date,
    AVG(france)  AS avg_france,
    AVG(germany) AS avg_germany,
    AVG(belgium) AS avg_belgium,
    AVG(spain)   AS avg_spain
FROM {{ ref('int_prices_hourly_wide') }}
GROUP BY date