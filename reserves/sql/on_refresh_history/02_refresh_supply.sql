WITH sucs AS (
    WITH u AS (

        WITH sues AS (
            SELECT
                last(id, id) AS id,
                id / 2,
                asset_id,
                SUM(balance_update) AS event_supply_update
                FROM balance_update_event
                GROUP BY id / 2, asset_id
        )
        SELECT sues.id, sues.asset_id, event_supply_update
            FROM sues
                     LEFT JOIN supply_history sh
                               ON sh.id = sues.id
            WHERE
                  sh.id IS NULL
              AND event_supply_update != 0

        UNION

        SELECT
            last(id, id) AS id,
            asset_id,
            last(supply, id) AS event_supply_update
            FROM supply_history
            GROUP BY asset_id
    )
    SELECT
        id,
        asset_id,
        SUM(SUM(event_supply_update)) OVER (
            PARTITION BY asset_id
            ORDER BY id
            ) AS supply
        FROM u
        WHERE
            event_supply_update != 0
        GROUP BY asset_id, id

)
INSERT
    INTO supply_history (id, asset_id, supply)
SELECT
    id,
    asset_id,
    supply
    FROM sucs
    WHERE
        sucs.id > (
            SELECT COALESCE(MAX(id), 0) AS id
                FROM supply_history
        );
