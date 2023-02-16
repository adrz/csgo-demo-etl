{{ config(materialized = 'table') }}

SELECT
    ds,
    "mapName" AS map,
    "matchID" AS match_id,
    string_agg(DISTINCT("tTeam"), ' vs '),
    count(*)
FROM
    rounds
GROUP BY
    ("mapName", "matchID", "ds")
