from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import DexKey, Pair, Pool, Asset
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.service.dex.lbp.lbp_service import LBPService
from dex_screener.types.hydradx.substrate_events.lbp_pool_created import LBPPoolCreatedPayload


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPPoolCreatedPayload],
) -> None:
    pool, _ = await Pool.update_or_create(
        account=event.payload['pool'],
        defaults={
            'dex_key': DexKey.LBP,
            'dex_pool_id': event.payload['pool'],
            'shares': '0',
        },
    )
    ctx.logger.info('Pool registered: %r.', pool)

    pair_id = pool.account
    if await Pair.exists(id=pair_id):
        ctx.logger.warning('Pair already exists: %s.', pair_id)
        return

    asset_a = await Asset.get(id=event.payload['data']['assets'][0])  # type: ignore[index]
    asset_b = await Asset.get(id=event.payload['data']['assets'][1])  # type: ignore[index]
    event_info = DexScreenerEventInfoDTO.from_event(event)

    pair = await Pair.create(
        id=pair_id,
        dex_key=DexKey.LBP,
        asset_0_id=min(asset_a.id, asset_b.id),
        asset_1_id=max(asset_a.id, asset_b.id),
        pool=pool,
        created_at_block_id=event_info.block_id,
        created_at_tx_id=event_info.tx_index,
        fee_bps=event.payload['data']['fee'][1],  # type: ignore[index]
    )
    ctx.logger.info('Pair registered in pool %r: %r.', pool, pair)

    await pool.assets.add(asset_a, asset_b)  # type: ignore[attr-defined]
    ctx.logger.info('Pair Assets added to pool %r: %s, %s.', pool, asset_a, asset_b)
