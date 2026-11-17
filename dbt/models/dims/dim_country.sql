-- Dimension: one row per bidding zone, with readable country names.
SELECT
    bidding_zone,
    country_code,
    country_name
FROM {{ ref('bidding_zones') }}