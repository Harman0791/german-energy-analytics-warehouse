-- Intermediate: hourly prices pivoted to one column per country.
-- Grain: one row per timestamp_utc. Feeds the wide-format marts.

{{ config(materialized='table') }}

SELECT
    timestamp_utc,
    date_local AS date,
    hour_local AS hour_of_day,
    MAX(price_eur_mwh) FILTER (WHERE bidding_zone = 'DE_LU') AS germany,
    MAX(price_eur_mwh) FILTER (WHERE bidding_zone = 'FR')    AS france,
    MAX(price_eur_mwh) FILTER (WHERE bidding_zone = 'ES')    AS spain,
    MAX(price_eur_mwh) FILTER (WHERE bidding_zone = 'BE')    AS belgium
FROM {{ ref('fct_dayahead_prices') }}
GROUP BY timestamp_utc, date_local, hour_local