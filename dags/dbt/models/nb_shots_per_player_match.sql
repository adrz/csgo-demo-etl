{{ config(materialized = 'table') }}

SELECT
    ds,
    "mapName" AS map,
    "matchID" AS match_id,
    "playerName" AS player,
    "weapon" AS weapon,
    count(*) as cnt
FROM
    weaponfires
GROUP BY
    ("mapName", "matchID", "ds", "playerName", "weapon")
