{{ config(materialized='table') }}

WITH tmp AS (
    SELECT
        "id" AS id,
        "attackerName" AS p1name,
        "victimName" AS p2name,
        1 AS p1score,
        0 AS p2score,
        ROW_NUMBER() OVER(ORDER BY (SELECT 1)) AS game_number
    FROM
        "kills"
    WHERE "attackerName" IS NOT NULL AND "victimName" IS NOT NULL
    ORDER BY (ds, tick)
)

SELECT
    "id" AS id,
    p1name,
    p2name,
    1 AS p1score,
    0 AS p2score,
    ROW_NUMBER() OVER(ORDER BY (SELECT 1)) AS game_number
FROM tmp
