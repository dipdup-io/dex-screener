from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent

from dex_screener.models import AssetPoolReserve
from dex_screener.models import DexKey
from dex_screener.models import Pair
from dex_screener.types.hydradx.substrate_events.lbp_liquidity_removed import LBPLiquidityRemovedPayload
from dex_screener.models import DexEvent
from dex_screener.models import DexScreenerEventType


async def on_liquidity_removed(
    ctx: HandlerContext,
    event: SubstrateEvent[LBPLiquidityRemovedPayload],
) -> None:
    dex_key = DexKey.LBP
    asset_0, asset_1 = int(event.payload['asset_a']), int(event.payload['asset_b'])
    amount_0, amount_1 = event.payload['amount_a'], event.payload['amount_b']

    if asset_0 > asset_1:
        asset_0, asset_1 = asset_1, asset_0
        amount_0, amount_1 = amount_1, amount_0

    pair = (
        await Pair.filter(
            dex_key=dex_key,
            asset_0_id=asset_0,
            asset_1_id=asset_1,
        )
        .prefetch_related('asset_0', 'asset_1', 'pool')
        .get()
    )

    reserves_0_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_0)
    reserves_1_model = await AssetPoolReserve.get(pool=pair.pool, asset=asset_1)

    amount_0 = pair.asset_0.from_minor(amount_0)
    amount_1 = pair.asset_1.from_minor(amount_1)
    reserves_0 = pair.asset_0.from_minor(reserves_0_model.reserve) - amount_0
    reserves_1 = pair.asset_1.from_minor(reserves_1_model.reserve) - amount_1

    reserves_0_model.reserve = str(reserves_0)
    reserves_1_model.reserve = str(reserves_1)
    await reserves_0_model.save()
    await reserves_1_model.save()

    await DexEvent(
        event_type=DexScreenerEventType.Exit,
        name=event.data.name,
        maker=event.payload['who'],
        pair=pair,
        amount_0_in=None,
        amount_1_in=None,
        amount_0_out=str(amount_0),
        amount_1_out=str(amount_1),
        price=None,
        amount_0=str(amount_0),
        amount_1=str(amount_1),
        asset_0_reserve=str(reserves_0),
        asset_1_reserve=str(reserves_1),
        event_index=event.data.index,
        tx_index=event.data.extrinsic_index if event.data.extrinsic_index is not None else 0,
        block_id=event.data.level,
    ).save()
    ctx.logger.debug(
        'Liquidity removed from pair %s: %s %s, %s %s.',
        pair.id,
        amount_0,
        pair.asset_0.symbol,
        amount_1,
        pair.asset_1.symbol,
    )
