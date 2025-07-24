"""
This module provides utility functions to interact with the reserves database.

Queries are simple, so we can avoid ORM and use raw SQL.
"""

import asyncio
import logging

from dipdup.database import get_connection

from dex_screener.models import Pair

_logger = logging.getLogger(__name__)


class NotFound(Exception):
    pass


def level_from_event_id(event_id: int) -> int:
    """
    Extracts the level from an event ID.
    The event ID is structured as (level << 17) + index.
    """
    return event_id >> 17


def event_ids_from_level(level: int) -> tuple[int, int]:
    """
    Returns the first and last event IDs for a given level.
    The first ID is (level << 17) + 1, and the last ID is (level + 1) << 17.
    """
    first_id = (level << 17) + 1
    last_id = (level + 1) << 17
    return first_id, last_id


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
        msg = f'No pool found for {pair_id=}'
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
        return int(res[1][0]['balance'])
    except IndexError as e:
        msg = f'No balance found for {asset_account=} at {level=}'
        raise NotFound(msg) from e


async def get_reserves_by_pair(
    pair: Pair,
    level: int,
) -> tuple[int, int]:
    await wait_for_reserves(level)

    reserves_0 = await get_balance_by_account(pair.pool.account, pair.asset_0.id, level)
    reserves_1 = await get_balance_by_account(pair.pool.account, pair.asset_1.id, level)

    if reserves_0 < 0 or reserves_1 < 0:
        msg = f'Negative reserves for {pair.id=} at {level=}: {reserves_0=}, {reserves_1=}'
        _logger.warning(msg)

    return reserves_0, reserves_1


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
        msg = f'No supply found for {asset_id=} at {level=}'
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
        msg = f'No decimals found for {asset_id=}'
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


async def get_transfers_by_level(
    level: int,
) -> list[dict]:
    """
    Returns transfers at the specified level.
    """
    conn = get_connection()
    sql = """
        SELECT * FROM reserves.balance_update_event
        WHERE id >= $1 AND id < $2
        ORDER BY id
    """
    first_id = (level << 17) + 1
    last_id = (level + 1) << 17
    args = (first_id, last_id)
    res = await conn.execute_query(sql, args)
    return res[1] if res else []
