-- NOTE: This was commented out as fails on full DB.
-- VACUUM ANALYSE balance_update_event, balance_history, supply_history;

-- NOTE: Updating internal table level to lower value because EventBuffer could be lost on restart. Should be safe.
WITH lse AS (
    SELECT id >> 17 AS last_level
        FROM balance_update_event
        ORDER BY id DESC
        LIMIT 1
)
UPDATE dipdup_index
SET level=lse.last_level
    FROM lse
    WHERE
          name = 'hydradx_events'
      AND level > lse.last_level;
