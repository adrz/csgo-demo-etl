{{ config(materialized='table') }}


WITH RECURSIVE p(current_game_number) AS (
  WITH players AS (
    SELECT DISTINCT p1name AS player_name
    FROM {{ ref('stg_elo') }}
    UNION
    SELECT DISTINCT p2name
    FROM {{ ref('stg_elo') }}
  )
  SELECT
    CAST(0 AS BIGINT)     AS game_number,
    player_name,
    1000.0 :: FLOAT AS previous_elo,
    1000.0 :: FLOAT AS new_elo
  FROM players
  UNION ALL
  (
    WITH previous_elos AS (
        SELECT *
        FROM p
    )
    SELECT
      {{ ref('stg_elo') }}.game_number,
      player_name,
      previous_elos.new_elo AS previous_elo,
      round(CASE WHEN player_name NOT IN (p1name, p2name)
        THEN previous_elos.new_elo
            WHEN player_name = p1name
              THEN previous_elos.new_elo + 32.0 * (p1score - (r1 / (r1 + r2)))
            ELSE previous_elos.new_elo + 32.0 * (p2score - (r2 / (r1 + r2))) END)
    FROM {{ ref('stg_elo') }}
      JOIN previous_elos
        ON current_game_number = {{ ref('stg_elo') }}.game_number - 1
      JOIN LATERAL (
           SELECT
             pow(10.0, (SELECT new_elo
                        FROM previous_elos
                        WHERE current_game_number = {{ ref('stg_elo') }}.game_number - 1 AND player_name = p1name) / 400.0) AS r1,
             pow(10.0, (SELECT new_elo
                        FROM previous_elos
                        WHERE current_game_number = {{ ref('stg_elo') }}.game_number - 1 AND player_name = p2name) / 400.0) AS r2
           ) r
        ON TRUE
  )
)
SELECT
  player_name,
  (
    SELECT new_elo
    FROM p
    WHERE t.player_name = p.player_name
    ORDER BY current_game_number DESC
    LIMIT 1
  )                    AS elo,
  count(CASE WHEN previous_elo < new_elo
    THEN 1
        ELSE NULL END) AS wins,
  count(CASE WHEN previous_elo > new_elo
    THEN 1
        ELSE NULL END) AS losses
FROM
  (
    SELECT *
    FROM p
    WHERE previous_elo <> new_elo
    ORDER BY current_game_number, player_name
  ) t
GROUP BY player_name
ORDER BY elo DESC