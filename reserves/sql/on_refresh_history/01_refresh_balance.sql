DROP TABLE IF EXISTS tmp_new_balance_update_event;
CREATE TEMP TABLE tmp_new_balance_update_event AS
WITH bhl AS (
    SELECT COALESCE(MAX(id), 0) AS id
        FROM balance_history
)
SELECT
    bue.id,
    asset_account,
    asset_id,
    account,
    balance_update
    FROM balance_update_event AS bue,
         bhl
    WHERE
        bue.id > bhl.id;
CREATE UNIQUE INDEX tmp_new_balance_update_event_pkey
    ON tmp_new_balance_update_event USING btree (id ASC);
ALTER TABLE tmp_new_balance_update_event
    ADD PRIMARY KEY USING INDEX tmp_new_balance_update_event_pkey;
CREATE INDEX idx_tmp_new_balance_update_event_asset_account
    ON tmp_new_balance_update_event USING btree (asset_account ASC);


DROP TABLE IF EXISTS tmp_new_balance_key;
CREATE TEMP TABLE tmp_new_balance_key AS
SELECT DISTINCT ON (asset_account) asset_account
    FROM tmp_new_balance_update_event
    ORDER BY asset_account;
CREATE INDEX idx_tmp_new_balance_key
    ON tmp_new_balance_key USING btree (asset_account ASC);


DROP TABLE IF EXISTS tmp_latest_balance;
CREATE TEMP TABLE tmp_latest_balance AS
SELECT DISTINCT ON (asset_account)
    asset_account,
    balance AS latest_balance
    FROM balance_history
    ORDER BY asset_account, id DESC;
CREATE INDEX idx_tmp_latest_balance
    ON tmp_latest_balance USING btree (asset_account ASC);


DROP TABLE IF EXISTS tmp_new_latest_balance;
CREATE TEMP TABLE tmp_new_latest_balance AS
SELECT
    asset_account,
    latest_balance
    FROM tmp_latest_balance AS lb
    JOIN tmp_new_balance_key AS ub
        USING (asset_account)
    ORDER BY asset_account;
CREATE INDEX idx_tmp_new_latest_balance
    ON tmp_new_latest_balance USING btree (asset_account ASC);


DROP TABLE IF EXISTS tmp_new_balance_update_with_latest_balance;
CREATE TEMP TABLE tmp_new_balance_update_with_latest_balance AS
SELECT
    bue.id,
    bue.asset_account,
    bue.asset_id,
    bue.account,
    bue.balance_update,
    lb.latest_balance
    FROM tmp_new_balance_update_event AS bue
        LEFT JOIN tmp_new_latest_balance AS lb USING (asset_account);
CREATE UNIQUE INDEX tmp_new_balance_update_with_latest_balance_pkey
    ON tmp_new_balance_update_with_latest_balance USING btree (id ASC);
ALTER TABLE tmp_new_balance_update_with_latest_balance
    ADD PRIMARY KEY USING INDEX tmp_new_balance_update_with_latest_balance_pkey;
CREATE INDEX idx_tmp_new_balance_update_with_latest_balance_key
    ON tmp_new_balance_update_with_latest_balance USING btree (asset_account);
CREATE INDEX idx_tmp_new_balance_update_with_latest_balance_distinct
    ON tmp_new_balance_update_with_latest_balance USING btree (asset_account, id);


WITH bucs AS (
    SELECT
        id,
        asset_account,
        last(asset_id, id) AS asset_id,
        last(account, id) AS account,
        COALESCE(last(latest_balance, id), 0)+SUM(SUM(balance_update)) OVER (
            PARTITION BY asset_account
            ORDER BY id
        ) AS balance
        FROM tmp_new_balance_update_with_latest_balance
        GROUP BY asset_account, id
)
INSERT
    INTO balance_history (id, asset_account, asset_id, account, balance)
SELECT
    id,
    asset_account,
    asset_id,
    account,
    balance
    FROM bucs;


DROP TABLE tmp_new_balance_update_event;
DROP TABLE tmp_new_balance_key;
DROP TABLE tmp_latest_balance;
DROP TABLE tmp_new_latest_balance;
DROP TABLE tmp_new_balance_update_with_latest_balance;
