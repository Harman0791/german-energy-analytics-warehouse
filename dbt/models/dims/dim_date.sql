-- Dimension: one row per calendar day, 2023 to 2027.
WITH spine AS (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2028-01-01' as date)"
    ) }}

)

SELECT
    date_day::date                        AS date,
    EXTRACT(YEAR    FROM date_day)::int   AS year,
    EXTRACT(QUARTER FROM date_day)::int   AS quarter,
    EXTRACT(MONTH   FROM date_day)::int   AS month,
    TO_CHAR(date_day, 'FMMonth')          AS month_name,
    EXTRACT(ISODOW  FROM date_day)::int   AS day_of_week,   -- 1 = Monday, 7 = Sunday
    TO_CHAR(date_day, 'FMDay')            AS weekday_name,
    EXTRACT(ISODOW  FROM date_day) >= 6   AS is_weekend
FROM spine