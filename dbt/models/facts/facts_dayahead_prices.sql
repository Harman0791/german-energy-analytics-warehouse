-- Fact table: one row per date and hour with prices per country.
-- Duplicates (DST) are already resolved in staging.

SELECT
    date,
    hour_of_day,
    year,
    month,
    day,
    weekday,
    france,
    italy,
    belgium,
    spain,
    germany
FROM {{ ref('stg_entsoe_dayahead_prices') }}