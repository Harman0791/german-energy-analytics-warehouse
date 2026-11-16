-- Staging: clean raw ENTSO-E day-ahead prices.
-- The raw data uses local time (CET/CEST), which causes two DST issues:
--   * spring: one hour that never existed (all prices NULL)
--   * autumn: one hour that happened twice (duplicate date + hour)
-- UK is excluded: separate market since Brexit and incomplete in this dataset.

WITH source AS (

    SELECT date, hour, belgium, france, germany, italy, spain
    FROM {{ source('energy_raw', 'entsoe_dayahead_prices') }}

),

-- Spring DST: drop the hour that never existed
existing_hours AS (

    SELECT *
    FROM source
    WHERE NOT (
        belgium IS NULL AND france IS NULL AND germany IS NULL
        AND italy IS NULL AND spain IS NULL
    )

),

-- Autumn DST: the repeated hour becomes one row (average of both)
deduplicated AS (

    SELECT
        date,
        hour,
        AVG(belgium) AS belgium,
        AVG(france)  AS france,
        AVG(germany) AS germany,
        AVG(italy)   AS italy,
        AVG(spain)   AS spain
    FROM existing_hours
    GROUP BY date, hour

)

SELECT
    date,
    hour,
    belgium,
    france,
    germany,
    italy,
    spain,

    -- Derived fields
    EXTRACT(YEAR  FROM date) AS year,
    EXTRACT(MONTH FROM date) AS month,
    EXTRACT(DAY   FROM date) AS day,
    TO_CHAR(date, 'Day')     AS weekday,
    hour                     AS hour_of_day

FROM deduplicated