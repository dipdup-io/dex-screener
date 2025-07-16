"""
This module provides utility functions to interact with the reserves database.

Queries are simple, so we can avoid ORM and use raw SQL.
"""

from dipdup.database import get_connection


class NotFound(Exception):
    pass


async def get_pool_by_pair(
    pair_id: str,
) -> tuple[int, int, str, int]:
    conn = get_connection()
    sql = """
        SELECT asset_0_id, asset_1_id, dex_pool.account, dex_pool.lp_token_id
        FROM reserves.dex_pair
        JOIN reserves.dex_pool ON dex_pair.dex_pool_id = dex_pool.id
        WHERE dex_pair.id = $1
    """
    res = await conn.execute_query(sql, pair_id)
    if not res:
        msg = f'No pool found for pair {pair_id}'
        raise NotFound(msg)
    return res[0]


async def get_balance_by_account(
    account: str,
    asset_id: int,
    level: int,
) -> str:
    sql = """
        SELECT balance FROM reserves.balance_history
        WHERE asset_account = $1 and id >= $2
        ORDER BY id DESC LIMIT 1
    """
    asset_account = f'{asset_id}:{account}'
    first_id = (level + 1) << 17
    args = (asset_account, first_id)

    conn = get_connection()
    res = await conn.execute_query(sql, args)
    if not res:
        msg = f'No balance found for account {account} at level {level}'
        raise NotFound(msg)
    return res[0]


async def get_asset_supply(
    asset_id: int,
    level: int,
) -> str:
    sql = """
        SELECT supply FROM reserves.supply_history
        WHERE asset_id = $1 AND id >= $2
        ORDER BY id DESC LIMIT 1
    """
    conn = get_connection()

    first_id = (level + 1) << 17
    args = (asset_id, first_id)

    res = await conn.execute_query(sql, args)
    if not res:
        msg = f'No supply found for asset {asset_id} at level {level}'
        raise NotFound(msg)
    return res[0]


async def get_decimals_by_asset_id(asset_id: int) -> int:
    conn = get_connection()
    sql = """
        SELECT decimals FROM reserves.dex_asset
        WHERE id = $1
    """
    res = await conn.execute_query(sql, asset_id)
    if not res:
        msg = f'No decimals found for asset {asset_id}'
        raise NotFound(msg)
    return res[0][0]
