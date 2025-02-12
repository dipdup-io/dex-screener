from __future__ import annotations

import logging
from itertools import combinations
from typing import TYPE_CHECKING

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.stableswap.const import DEX_PULL_ACCOUNT_MAPPING

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.types.hydradx.substrate_events.stableswap_pool_created import StableswapPoolCreatedPayload


class StableSwapService:
    logger = logging.getLogger('stableswap_service')

    @classmethod
    def get_pair_id(cls, pool_account: str, asset_a_id: int, asset_b_id: int) -> str:
        asset_id_list = [str(asset_id) for asset_id in sorted([int(asset_a_id), int(asset_b_id)])]

        return '-'.join([pool_account, *asset_id_list])

    @classmethod
    async def register_pool(cls, event: SubstrateEvent[StableswapPoolCreatedPayload]):
        dex_pool_id = event.payload['pool_id']
        account = DEX_PULL_ACCOUNT_MAPPING[int(dex_pool_id)]
        pool = await Pool.create(
            dex_key=DexKey.StableSwap,
            dex_pool_id=dex_pool_id,
            account=account,
            lp_token_id=dex_pool_id,
        )
        cls.logger.info('StableSwap Pool registered: %r.', pool)

        return pool

    @classmethod
    async def register_pair(cls, pool: Pool, event: SubstrateEvent[StableswapPoolCreatedPayload]):

        for asset_a_id, asset_b_id in combinations(event.payload['assets'], 2):
            pair_id = cls.get_pair_id(pool.account, asset_a_id, asset_b_id)

            event_info = DexScreenerEventInfoDTO.from_event(event)

            pair = await Pair.create(
                id=pair_id,
                dex_key=DexKey.StableSwap,
                asset_0_id=min(asset_a_id, asset_b_id),
                asset_1_id=max(asset_a_id, asset_b_id),
                pool=pool,
                created_at_block_id=event_info.block_id,
                created_at_txn_id=event_info.tx_id,
                fee_bps=event.payload['fee'],
            )
            cls.logger.info('Pair registered in pool %r: %r.', pool, pair)
        pool_assets: list[Asset] = await Asset.filter(id__in=event.payload['assets'])
        await pool.assets.add(*pool_assets)
        cls.logger.info('Assets added to pool %r: %s.', pool, pool_assets)
