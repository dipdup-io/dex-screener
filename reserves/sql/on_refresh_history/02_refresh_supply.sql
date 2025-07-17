/*
 * Supply History Refresh Script
 * 
 * This script processes balance update events to calculate asset supply totals.
 * It performs an incremental update by only processing events that have occurred
 * since the last supply history update.
*/

-- Step 1: Extract new supply update events
-- Creates a temporary table containing only events that haven't been processed yet
DROP TABLE IF EXISTS tmp_new_supply_update_event;
CREATE TEMP TABLE tmp_new_supply_update_event AS
WITH shl AS (
    -- Get the highest ID from supply_history to determine the processing checkpoint
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
-- Create indexes for optimal query performance
CREATE UNIQUE INDEX tmp_new_supply_update_event_pkey
    ON tmp_new_supply_update_event USING btree (id ASC);
ALTER TABLE tmp_new_supply_update_event
    ADD PRIMARY KEY USING INDEX tmp_new_supply_update_event_pkey;
-- Index for asset_id lookups used in subsequent joins
CREATE INDEX idx_tmp_new_supply_update_event_asset_id_btree
    ON tmp_new_supply_update_event USING btree (asset_id);


-- Step 2: Extract unique asset IDs that need supply updates
-- This creates a lookup table for assets that have new supply events
DROP TABLE IF EXISTS tmp_new_supply_key;
CREATE TEMP TABLE tmp_new_supply_key AS
SELECT DISTINCT asset_id
    FROM tmp_new_supply_update_event;
-- Dual indexing strategy: hash for equality checks, btree for range queries
CREATE INDEX idx_tmp_new_supply_key
    ON tmp_new_supply_key USING hash (asset_id);
CREATE INDEX idx_tmp_new_supply_key_btree
    ON tmp_new_supply_key USING btree (asset_id);


-- Step 3: Get the latest supply for each asset from supply_history
-- This retrieves the most recent supply state for assets that need updates
DROP TABLE IF EXISTS tmp_updated_supply;
CREATE TEMP TABLE tmp_updated_supply AS
    SELECT
    public.last(bh.id, bh.id) AS id,
    public.last(bh.asset_id, bh.id) AS asset_id,
    public.last(supply, bh.id) AS balance_update
    FROM supply_history AS bh
         JOIN tmp_new_supply_key AS ub USING (asset_id)
    GROUP BY bh.asset_id;


-- Step 4: Add existing supply data to the events table
-- This ensures we have baseline supply values for calculation
INSERT
    INTO tmp_new_supply_update_event (id, asset_id, balance_update)
SELECT id, asset_id, balance_update
    FROM tmp_updated_supply;


-- Step 5: Calculate running supplies and insert into supply_history
-- This is the core calculation that computes cumulative supplies using window functions
WITH sucs AS (
    -- Inner CTE: Group events by key (id/2) and asset_id to handle duplicates
    WITH sues AS (
        SELECT
            public.last(id, id) AS id,
            id / 2 AS key,  -- Key-based grouping to manage event deduplication
            asset_id,
            SUM(balance_update) AS event_supply_update
            FROM tmp_new_supply_update_event
            GROUP BY key, asset_id
    )
    -- Outer CTE: Calculate running totals using window functions
    SELECT
        id,
        asset_id,
        SUM(SUM(event_supply_update)) OVER (
            PARTITION BY asset_id
            ORDER BY id
            ) AS supply
        FROM sues
        WHERE
            event_supply_update != 0  -- Filter out zero-change events
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
        -- Only insert records newer than the current supply_history
        sucs.id > (
            SELECT COALESCE(MAX(id), 0) AS id
                FROM supply_history
        );


-- Step 6: Cleanup temporary tables
-- Remove all temporary tables to free up memory
DROP TABLE tmp_new_supply_update_event;
DROP TABLE tmp_new_supply_key;
DROP TABLE tmp_updated_supply;
