-- Fact: hourly day-ahead price per bidding zone.
-- Grain: one row per timestamp_utc and bidding_zone.
-- Foreign keys: bidding_zone -> dim_country, date_local -> dim_date.

{{ config(materialized='table') }}

SELECT
    timestamp_utc,
    bidding_zone,
    date_local,
    hour_local,
    price_eur_mwh
FROM {{ ref('stg_dayahead_prices') }}