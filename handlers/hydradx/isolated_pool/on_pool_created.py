from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import Asset
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.models import Pool
from dex_screener.models.dex_fields import Account
from dex_screener.models.dto import DexScreenerEventInfoDTO
from dex_screener.types.hydradx.substrate_events.xyk_pool_created import XYKPoolCreatedPayload

# FIXME: Why?
XYK_GET_EXCHANGE_FEE_BPS = 30


async def on_pool_created(
    ctx: HandlerContext,
    event: SubstrateEvent[XYKPoolCreatedPayload],
) -> None:
    # NOTE: Pool can be destroyed and recreated later. We don't need to process this event because shares=0.
    account = Account(event.payload['pool'])
    pool, _ = await Pool.update_or_create(
        account=account,
        defaults={
            'dex_key': DexKey.IsolatedPool,
            'dex_pool_id': event.payload['pool'],
            'lp_token_id': event.payload['share_token'],
        },
    )

    ctx.logger.info('Pool registered: %r.', pool)

    pair_id = pool.account
    asset_a = await Asset.get(id=event.payload['asset_a'])
    asset_b = await Asset.get(id=event.payload['asset_b'])
    event_info = DexScreenerEventInfoDTO.from_event(event)

    if not await Pair.exists(id=pair_id):
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
        ctx.logger.info('Pair registered in pool %r: %r.', pool, pair)
