WITH bucs AS (
    WITH u AS (
        SELECT
            bue.id,
            bue.account,
            bue.asset_id,
            balance_update
            FROM balance_update_event bue
                     LEFT JOIN balance_history bh ON bue.id = bh.id
            WHERE
                bh.id IS NULL

        UNION

        SELECT
            last(id, id) AS id,
            account,
            asset_id,
            last(balance, id) AS balance_update
            FROM balance_history
            GROUP BY account, asset_id
    )
    SELECT
        id,
        account,
        asset_id,
        SUM(SUM(balance_update)) OVER (
            PARTITION BY account, asset_id
            ORDER BY id
            ) AS balance
        FROM u
        GROUP BY account, asset_id, id
)
INSERT
    INTO balance_history (id, account, asset_id, balance)
SELECT
    id,
    account,
    asset_id,
    balance
    FROM bucs
    WHERE
        bucs.id > (
            SELECT COALESCE(MAX(id), 0) AS id
                FROM balance_history
        );
