-- Hourly price spread between Germany and its neighbours.

SELECT
    timestamp_utc,
    date,
    hour_of_day,
    germany - france  AS de_vs_fr,
    germany - spain   AS de_vs_es,
    germany - belgium AS de_vs_be
FROM {{ ref('int_prices_hourly_wide') }}