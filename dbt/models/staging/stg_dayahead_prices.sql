-- Staging: ENTSO-E day-ahead prices from the API, one row per hour and bidding zone.
-- timestamp_utc is the key. Local time is added for analysis only:
-- in October one local hour occurs twice, so local time can never be a key.

WITH source AS (

    SELECT * FROM {{ source('energy_raw', 'raw_dayahead_prices') }}

),

renamed AS (

    SELECT
        timestamp_utc,
        bidding_zone,
        price_eur_mwh,

        -- Local wall-clock time (all four zones use Central European Time)
        timestamp_utc AT TIME ZONE 'Europe/Berlin'                       AS timestamp_local,
        (timestamp_utc AT TIME ZONE 'Europe/Berlin')::date               AS date_local,
        EXTRACT(HOUR FROM timestamp_utc AT TIME ZONE 'Europe/Berlin')::int AS hour_local

    FROM source

)

SELECT * FROM renamed