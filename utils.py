"""
This module provides utility functions to interact with the reserves database.

Queries are simple, so we can avoid ORM and use raw SQL.
"""

import asyncio
import logging

from dipdup.database import get_connection

_logger = logging.getLogger(__name__)


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
    try:
        return res[1][0]
    except IndexError as e:
        msg = f'No pool found for pair {pair_id}'
        raise NotFound(msg) from e


async def get_balance_by_account(
    account: str,
    asset_id: int,
    level: int,
) -> int:
    sql = """
        SELECT balance FROM reserves.balance_history
        WHERE asset_account = $1 and id < $2
        ORDER BY id DESC LIMIT 1
    """
    asset_account = f'{asset_id}:{account}'
    last_id = (level + 1) << 17
    args = (asset_account, last_id)

    conn = get_connection()
    res = await conn.execute_query(sql, args)
    try:
        return res[1][0]['balance']
    except IndexError as e:
        msg = f'No balance found for account {account} at level {level}'
        raise NotFound(msg) from e


async def get_asset_supply(
    asset_id: int,
    level: int,
) -> int:
    sql = """
        SELECT supply FROM reserves.supply_history
        WHERE asset_id = $1 AND id < $2
        ORDER BY id DESC LIMIT 1
    """
    conn = get_connection()

    last_id = (level + 1) << 17
    args = (asset_id, last_id)

    res = await conn.execute_query(sql, args)
    try:
        return res[1][0]['supply']
    except IndexError as e:
        msg = f'No supply found for asset {asset_id} at level {level}'
        raise NotFound(msg) from e


async def get_decimals_by_asset_id(asset_id: int) -> int:
    conn = get_connection()
    sql = """
        SELECT decimals FROM reserves.dex_asset
        WHERE id = $1
    """
    res = await conn.execute_query(sql, asset_id)
    try:
        return res[1][0]['decimals']
    except IndexError as e:
        msg = f'No decimals found for asset {asset_id}'
        raise NotFound(msg) from e


async def get_balance_history_head() -> int:
    """
    Returns level of the last balance history record.
    """
    conn = get_connection()
    sql = """
        SELECT id FROM reserves.balance_history
        ORDER BY id DESC LIMIT 1
    """
    res = await conn.execute_query(sql)
    try:
        return res[1][0]['id'] >> 17
    except IndexError:
        return 0


async def get_supply_history_head() -> int:
    """
    Returns level of the last supply history record.
    """
    conn = get_connection()
    sql = """
        SELECT id FROM reserves.supply_history
        ORDER BY id DESC LIMIT 1
    """
    res = await conn.execute_query(sql)
    try:
        return res[1][0]['id'] >> 17
    except IndexError:
        return 0


async def wait_for_reserves(level: int) -> None:
    """
    Waits for reserves to be updated to the specified level.
    """
    while True:
        reserves_head = min(
            await get_balance_history_head(),
            await get_supply_history_head(),
        )
        if reserves_head >= level:
            return

        _logger.info('Reserves indexer is behind, waiting for update...')
        await asyncio.sleep(5)
