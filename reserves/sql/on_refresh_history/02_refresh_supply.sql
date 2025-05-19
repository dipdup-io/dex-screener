DROP TABLE IF EXISTS tmp_new_supply_update_event;
CREATE TEMP TABLE tmp_new_supply_update_event AS
WITH shl AS (
    SELECT COALESCE(MAX(id), 0) AS id
        FROM supply_history
)
SELECT
    bue.id,
    asset_id,
    balance_update
    FROM balance_update_event AS bue,
         shl
    WHERE
        bue.id > shl.id;
CREATE UNIQUE INDEX tmp_new_supply_update_event_pkey
    ON tmp_new_supply_update_event USING btree (id ASC);
ALTER TABLE tmp_new_supply_update_event
    ADD PRIMARY KEY USING INDEX tmp_new_supply_update_event_pkey;
CREATE INDEX idx_tmp_new_supply_update_event_asset_id_btree
    ON tmp_new_supply_update_event USING btree (asset_id);


DROP TABLE IF EXISTS tmp_new_supply_key;
CREATE TEMP TABLE tmp_new_supply_key AS
SELECT DISTINCT asset_id
    FROM tmp_new_supply_update_event;
CREATE INDEX idx_tmp_new_supply_key
    ON tmp_new_supply_key USING hash (asset_id);
CREATE INDEX idx_tmp_new_supply_key_btree
    ON tmp_new_supply_key USING btree (asset_id);


DROP TABLE IF EXISTS tmp_updated_supply;
CREATE TEMP TABLE tmp_updated_supply AS
    SELECT
    last(bh.id, bh.id) AS id,
    last(bh.asset_id, bh.id) AS asset_id,
    last(supply, bh.id) AS balance_update
    FROM supply_history AS bh
         JOIN tmp_new_supply_key AS ub USING (asset_id)
    GROUP BY bh.asset_id;


INSERT
    INTO tmp_new_supply_update_event (id, asset_id, balance_update)
SELECT id, asset_id, balance_update
    FROM tmp_updated_supply;


WITH sucs AS (
    WITH sues AS (
        SELECT
            last(id, id) AS id,
            id / 2 AS key,
            asset_id,
            SUM(balance_update) AS event_supply_update
            FROM tmp_new_supply_update_event
            GROUP BY key, asset_id
    )
    SELECT
        id,
        asset_id,
        SUM(SUM(event_supply_update)) OVER (
            PARTITION BY asset_id
            ORDER BY id
            ) AS supply
        FROM sues
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


DROP TABLE tmp_new_supply_update_event;
DROP TABLE tmp_new_supply_key;
DROP TABLE tmp_updated_supply;
