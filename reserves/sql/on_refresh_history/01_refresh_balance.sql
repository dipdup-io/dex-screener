/*
 * This script processes new balance update events and calculates running balance totals
 * for each asset account. It performs an incremental update by only processing events
 * that have occurred since the last balance history update.
 */

-- Step 1: Extract new balance update events
-- Creates a temporary table containing only events that haven't been processed yet
DROP TABLE IF EXISTS tmp_new_balance_update_event;
CREATE TEMP TABLE tmp_new_balance_update_event AS
WITH bhl AS (
    -- Get the highest ID from balance_history to determine the processing checkpoint
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
-- Create indexes for optimal query performance
CREATE UNIQUE INDEX tmp_new_balance_update_event_pkey
    ON tmp_new_balance_update_event USING btree (id ASC);
ALTER TABLE tmp_new_balance_update_event
    ADD PRIMARY KEY USING INDEX tmp_new_balance_update_event_pkey;
-- Index for asset_account lookups used in subsequent joins
CREATE INDEX idx_tmp_new_balance_update_event_asset_account
    ON tmp_new_balance_update_event USING btree (asset_account ASC);


-- Step 2: Extract unique asset accounts that need balance updates
-- This creates a lookup table for accounts that have new balance events
DROP TABLE IF EXISTS tmp_new_balance_key;
CREATE TEMP TABLE tmp_new_balance_key AS
SELECT DISTINCT ON (asset_account) asset_account
    FROM tmp_new_balance_update_event
    ORDER BY asset_account;
CREATE INDEX idx_tmp_new_balance_key
    ON tmp_new_balance_key USING btree (asset_account ASC);


-- Step 3: Get the latest balance for each asset account from balance_history
-- This retrieves the most recent balance state for accounts that need updates
DROP TABLE IF EXISTS tmp_latest_balance;
CREATE TEMP TABLE tmp_latest_balance AS
SELECT DISTINCT ON (asset_account)
    asset_account,
    balance AS latest_balance
    FROM balance_history
    ORDER BY asset_account, id DESC;
CREATE INDEX idx_tmp_latest_balance
    ON tmp_latest_balance USING btree (asset_account ASC);


-- Step 4: Join latest balances with accounts that have new events
-- This creates a mapping of starting balances for accounts with new updates
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


-- Step 5: Combine new balance events with their starting balances
-- This creates the final working table with all necessary data for balance calculation
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
-- Multiple indexes for different query patterns in the final calculation
CREATE UNIQUE INDEX tmp_new_balance_update_with_latest_balance_pkey
    ON tmp_new_balance_update_with_latest_balance USING btree (id ASC);
ALTER TABLE tmp_new_balance_update_with_latest_balance
    ADD PRIMARY KEY USING INDEX tmp_new_balance_update_with_latest_balance_pkey;
CREATE INDEX idx_tmp_new_balance_update_with_latest_balance_key
    ON tmp_new_balance_update_with_latest_balance USING btree (asset_account);
CREATE INDEX idx_tmp_new_balance_update_with_latest_balance_distinct
    ON tmp_new_balance_update_with_latest_balance USING btree (asset_account, id);


-- Step 6: Calculate running balances and insert into balance_history
-- This is the core calculation that computes cumulative balances using window functions
WITH bucs AS (
    SELECT
        id,
        asset_account,
        -- Use the last known asset_id and account for each group
        public.last(asset_id, id) AS asset_id,
        public.last(account, id) AS account,
        -- Calculate running balance: starting balance + cumulative sum of updates
        COALESCE(public.last(latest_balance, id), 0)+SUM(SUM(balance_update)) OVER (
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


-- Step 7: Cleanup temporary tables
-- Remove all temporary tables to free up memory
DROP TABLE tmp_new_balance_update_event;
DROP TABLE tmp_new_balance_key;
DROP TABLE tmp_latest_balance;
DROP TABLE tmp_new_latest_balance;
DROP TABLE tmp_new_balance_update_with_latest_balance;
