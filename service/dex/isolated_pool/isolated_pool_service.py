from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.isolated_pool.const import XYK_GET_EXCHANGE_FEE_BPS

if TYPE_CHECKING:
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


class IsolatedPoolService:
    logger = logging.getLogger('isolated_pool_service')

    @classmethod
    async def register_pool(cls, event: SubstrateEvent[XYKPoolCreatedPayload]):
        pool, _ = await Pool.update_or_create(
            account=event.payload['pool'],
            defaults={
                'dex_key': DexKey.IsolatedPool,
                'dex_pool_id': event.payload['pool'],
                'lp_token_id': event.payload['share_token'],
            },
        )
        cls.logger.info('Pool registered: %r.', pool)

        return pool

    @classmethod
    async def register_pair(cls, pool: Pool, event: SubstrateEvent[XYKPoolCreatedPayload]):
        pair_id = pool.account
        if await Pair.exists(id=pair_id):
            cls.logger.warning('Pair already exists: %s.', pair_id)
            return

        asset_a = await Asset.get(id=event.payload['asset_a'])
        asset_b = await Asset.get(id=event.payload['asset_b'])
        event_info = DexScreenerEventInfoDTO.from_event(event)

        pair = await Pair.create(
            id=pair_id,
            dex_key=DexKey.IsolatedPool,
            asset_0_id=min(asset_a.id, asset_b.id),
            asset_1_id=max(asset_a.id, asset_b.id),
            pool=pool,
            created_at_block_id=event_info.block_id,
            created_at_tx_id=event_info.tx_index,
            fee_bps=XYK_GET_EXCHANGE_FEE_BPS,
        )
        cls.logger.info('Pair registered in pool %r: %r.', pool, pair)

        await pool.assets.add(asset_a, asset_b)  # type: ignore[attr-defined]
        cls.logger.info('Pair Assets added to pool %r: %s, %s.', pool, asset_a, asset_b)
