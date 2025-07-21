from __future__ import annotations

from typing import TYPE_CHECKING

from dex_screener.utils import NotFound
from dex_screener.utils import get_transfers_by_level

if TYPE_CHECKING:
    from dex_screener.models import Pool

DEX_POOL_ACCOUNT_MAPPING: dict[int, str] = {
    100: '0x22bb00df7706a5965728b60f96406ee59ce675fd5fd10652a4ed6f618856ccfe',
    101: '0xaffeef2e0ccac1986d8ac3b557e1e0d682d649bf61aee81e1a7faaab7eae35e0',
    102: '0x7fe7d370617e793b178de6efc9bc5813382f2e2866ee298ea1917d8b8dce436b',
    690: '0xe21da918e4176b72ef1930ffaa17edcb03b9b739c2843fb0cf096283a7d9c261',
    4200: '0x0c34f5f4950f3bf6c57da86062a40e0c55f0b74e5f6a571f11f5de30dd522bab',
    103: '0x3dcb0e0f4664245edf656ac63f64805c14e18c690b375e7ff09e01f21ac3abbd'
}

_pool_accounts: dict[int, str] = {}


def get_pair_id(pool: Pool, asset_a_id: int, asset_b_id: int) -> str:
    asset_id_list = [
        str(asset_id) for asset_id in sorted([int(asset_a_id), int(asset_b_id)]) if asset_id != pool.lp_token_id
    ]

    return '-'.join([pool.account, *asset_id_list])


async def get_pool_account(pool_id: int, level: int) -> str:
    # FIXME:
    return DEX_POOL_ACCOUNT_MAPPING[pool_id]

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
