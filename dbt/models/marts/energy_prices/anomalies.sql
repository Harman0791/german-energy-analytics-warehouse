-- Flags hours where the price deviates more than 20 EUR/MWh
-- from its 24-hour rolling average.

WITH enriched AS (

    SELECT
        timestamp_utc,
        date,
        hour_of_day,
        france,
        germany,
        AVG(france)  OVER w AS france_ra,
        AVG(germany) OVER w AS germany_ra
    FROM {{ ref('int_prices_hourly_wide') }}
    WINDOW w AS (ORDER BY timestamp_utc ROWS BETWEEN 23 PRECEDING AND CURRENT ROW)

)

SELECT
    timestamp_utc,
    date,
    hour_of_day,
    france,
    france_ra,
    france - france_ra             AS france_deviation,
    ABS(france - france_ra) > 20   AS france_anomaly,
    germany,
    germany_ra,
    germany - germany_ra           AS germany_deviation,
    ABS(germany - germany_ra) > 20 AS germany_anomaly
FROM enriched