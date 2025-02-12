from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.omnipool.const import OMNIPOOL_HUB_ASSET_ID
from dex_screener.service.dex.omnipool.const import OMNIPOOL_SYSTEM_ACCOUNT

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.types.hydradx.substrate_events.omnipool_token_added import OmnipoolTokenAddedPayload


class OmnipoolService:
    logger = logging.getLogger('omnipool_service')

    @classmethod
    def get_pair_id(cls, asset_a_id: int, asset_b_id: int) -> str:
        asset_id_list = [str(asset_id) for asset_id in sorted([int(asset_a_id), int(asset_b_id)]) if asset_id != OMNIPOOL_HUB_ASSET_ID]

        return '-'.join([OMNIPOOL_SYSTEM_ACCOUNT, *asset_id_list])

    @classmethod
    async def get_pool(cls):
        pool = await Pool.get_or_none(account=OMNIPOOL_SYSTEM_ACCOUNT)
        if pool is None:
            pool = await cls.register_pool()
        return pool

    @classmethod
    async def register_pool(cls):
        pool = await Pool.create(
            dex_key=DexKey.Omnipool,
            dex_pool_id = OMNIPOOL_SYSTEM_ACCOUNT,
            account=OMNIPOOL_SYSTEM_ACCOUNT,
        )
        cls.logger.info('Omnipool registered: %r.', pool)

        base_asset = await Asset.get(id=OMNIPOOL_HUB_ASSET_ID)
        await pool.assets.add(base_asset)
        cls.logger.info('Omnipool Base Asset added to pool %r: %s.', pool, base_asset)

        return pool

    @classmethod
    async def register_pair(cls, pool: Pool, event: SubstrateEvent[OmnipoolTokenAddedPayload]):
        new_asset = await Asset.get(id=event.payload['asset_id'])
        async for pool_asset in pool.assets:
            if pool_asset.id == new_asset.id:
                continue
            pair_id = cls.get_pair_id(new_asset.id, pool_asset.id)

            if await Pair.exists(id=pair_id):
                cls.logger.warning('Pair already exists: %s.', pair_id)
                continue

            event_info = DexScreenerEventInfoDTO.from_event(event)

            pair = await Pair.create(
                id=pair_id,
                dex_key=DexKey.Omnipool,
                asset_0_id=min(pool_asset.id, new_asset.id),
                asset_1_id=max(pool_asset.id, new_asset.id),
                pool=pool,
                created_at_block_id=event_info.block_id,
                created_at_txn_id=event_info.tx_id,
                # fee_bps=None,
            )
            cls.logger.info('Pair registered in pool %r: %r.', pool, pair)

        await pool.assets.add(new_asset)
        cls.logger.info('Pair Asset added to pool %r: %s.', pool, new_asset)
