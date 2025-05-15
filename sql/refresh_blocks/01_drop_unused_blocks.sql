ALTER TABLE dex_block DISABLE TRIGGER ALL;

WITH cte AS (
    SELECT b.level
    FROM dex_block b
    LEFT JOIN dex_asset a ON b.level = a.updated_at_block_id
    LEFT JOIN dex_pair p ON b.level = p.created_at_block_id
    LEFT JOIN dex_event s ON b.level = s.block_id
    WHERE
        a.id ISNULL AND p.id ISNULL AND s.id ISNULL
    LIMIT 10000
)
DELETE FROM dex_block
USING cte
WHERE dex_block.level = cte.level;

ALTER TABLE dex_block ENABLE TRIGGER ALL;
