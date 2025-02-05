from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    pool, _ = await Pool.update_or_create(
        id=event.payload['pool'],
        defaults={
            'account': event.payload['pool'],
            'dex_key': DexKey.IsolatedPool,
            'lp_token_id': event.payload['share_token'],
        },
    )

    asset_a = await Asset.get(id=event.payload['asset_a'])
    asset_b = await Asset.get(id=event.payload['asset_b'])
    await pool.assets.add(asset_a, asset_b)

    event_info = DexScreenerEventInfoDTO.from_event(event)

    pair_id = event.payload['pool']
    if not await Pair.exists(id=pair_id):
        pair = await Pair.create(
            id=pair_id,
            dex_key=pool.dex_key,
            asset_0_id=min(asset_a.id, asset_b.id),
            asset_1_id=max(asset_a.id, asset_b.id),
            pool=pool,
            created_at_block_id=event_info.block_id,
            created_at_txn_id=event_info.tx_id,
            # fee_bps
        )
        ctx.logger.info('Pair created: %s.', pair.id)
    else:
        ctx.logger.warning('Pair already exists: %s.', pair_id)
