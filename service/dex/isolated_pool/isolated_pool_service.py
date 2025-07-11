from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dex_screener.models import Asset
from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.isolated_pool.const import XYK_GET_EXCHANGE_FEE_BPS

if TYPE_CHECKING:
    from aiosubstrate import SubstrateInterface
    from dipdup.models.substrate import SubstrateEvent

    from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


class IsolatedPoolService:
    logger = logging.getLogger('isolated_pool_service')

    @classmethod
    async def register_pool(cls, event: SubstrateEvent[XYKPoolCreatedPayload]):
        # NOTE: update because pool can be destroyed and recreated
        pool, _ = await Pool.update_or_create(
            account=event.payload['pool'],
            defaults={
                'dex_key': DexKey.IsolatedPool,
                'dex_pool_id': event.payload['pool'],
                'lp_token_id': event.payload['share_token'],
                'shares': str(event.payload['initial_shares_amount']),
            },
        )
        cls.logger.info('Pool registered: %r.', pool)

        return pool

    @classmethod
    async def register_pair(cls, ctx, pool: Pool, event: SubstrateEvent[XYKPoolCreatedPayload]):
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

        # FIXME: We need to fetch initial pool transfers to calculate share prices later
        reserves_a_model = await AssetPoolReserve.get(pool=pool, asset=asset_a.id)
        reserves_b_model = await AssetPoolReserve.get(pool=pool, asset=asset_b.id)

        node = ctx.datasources['node']
        interface: SubstrateInterface = node._interface

        block_hash = await interface.get_block_hash(event.data.block_number)
        block_events = await interface.get_events(block_hash)

        transfers = {}
        for block_event in block_events:
            e = block_event.value
            if (e['module_id'], e['event_id']) == ('Tokens', 'Transfer'):
                if e['attributes']['to'] != interface.ss58_encode(pool.account):
                    continue
                transfers[e['attributes']['currency_id']] = e['attributes']['amount']
            elif (e['module_id'], e['event_id']) == ('Balances', 'Transfer'):
                if e['attributes']['to'] != interface.ss58_encode(pool.account):
                    continue
                transfers[0] = e['attributes']['amount']

        for asset_id, value in transfers.items():
            if asset_id == asset_a.id:
                reserves_a_model.reserve = str(asset_a.from_minor(value))
            elif asset_id == asset_b.id:
                reserves_b_model.reserve = str(asset_b.from_minor(value))

        assert len(transfers) == 2

        await reserves_a_model.save()
        await reserves_b_model.save()
