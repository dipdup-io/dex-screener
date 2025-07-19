from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.utils import NotFound
from dex_screener.utils import get_transfers_by_level

if TYPE_CHECKING:
    from dex_screener.models import Pool

_pool_accounts = {}


def get_pair_id(pool: Pool, asset_a_id: int, asset_b_id: int) -> str:
    asset_id_list = [
        str(asset_id) for asset_id in sorted([int(asset_a_id), int(asset_b_id)]) if asset_id != pool.lp_token_id
    ]

    return '-'.join([pool.account, *asset_id_list])


async def get_pool_account(pool_id: int, level: int) -> str:
    if pool_id in _pool_accounts:
        return _pool_accounts[pool_id]

    transfers = await get_transfers_by_level(level)
    for transfer in transfers:
        _token_id, account = transfer['asset_account'].split(':')
        if int(_token_id) == pool_id:
            _pool_accounts[pool_id] = account
            return account
    msg = f'No transfers found for {pool_id=}'
    raise NotFound(msg)
