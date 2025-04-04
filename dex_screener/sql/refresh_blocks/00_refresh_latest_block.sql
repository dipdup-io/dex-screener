WITH elb AS (
    SELECT
        b.level AS block_number,
        b.timestamp AS block_timestamp
    FROM dex_event AS e
    JOIN dex_block AS b ON b.level = e.block_id
    WHERE b.timestamp IS NOT NULL
    ORDER BY e.id DESC
    LIMIT 1
)
UPDATE ds_latest_block
SET
    block_number=elb.block_number,
    block_timestamp=elb.block_timestamp
FROM elb
WHERE id=True;
